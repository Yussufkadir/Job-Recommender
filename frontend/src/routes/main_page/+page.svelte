<script lang="ts">
	import { API_BASE, getRecommendations, type Job } from '$lib/api';
	import { authFetch } from '$lib/auth';

	let cvText = '';
	let skillsInput = '';
	let seniorityLevel = 'All';
	let query = '';
	let jobs: Job[] = [];
	let loading = false;
	let error = '';
	let cvFile: File | null = null;
	let tailoringJobId: string | null = null;
	let tailoredResults: Record<string, string> = {};

	async function handleFileSelect(event: Event) {
		const target = event.target as HTMLInputElement;
		if (target.files && target.files.length > 0) {
			cvFile = target.files[0];

			const formData = new FormData();
			formData.append('file', cvFile);

			cvText = 'Extracting text from file...';
			skillsInput = 'Extracting...';

			try {
				const res = await authFetch(`${API_BASE}/api/parse_cv`, {
					method: 'POST',
					body: formData
				});

				if (res.ok) {
					const data = await res.json();
					cvText = data.text;

					if (data.skills && data.skills.length > 0) {
						skillsInput = data.skills.join(', ');
					} else {
						skillsInput = '';
					}
				} else {
					cvText = '';
					alert('failed to read file text.');
				}
			} catch (e) {
				console.error(e);
				cvText = '';
				alert('Error parsing file.');
			}
		}
	}

	async function handleSearch() {
		if (!cvText && !skillsInput) {
			error = 'Please fill in both CV content and Skills.';
			return;
		}

		if (!query) {
			error = 'Please enter a job title to find a relevant job.';
			return;
		}

		loading = true;
		error = '';
		jobs = [];

		const skillsArray = skillsInput
			.split(',')
			.map((s) => s.trim())
			.filter((s) => s.length > 0);

		try {
			const response = await getRecommendations(cvText, query, skillsArray, seniorityLevel);
			jobs = response.jobs;
		} catch (err) {
			console.error(err);
			error = 'Failed to fetch jobs. Check the backend.';
		} finally {
			loading = false;
		}
	}

	async function handleTailorCV(job: Job) {
		if (!cvFile) {
			alert('Please upload a CV file (PDF/DOCX) in the top section first.');
			return;
		}

		tailoringJobId = job.title;

		try {
			const formData = new FormData();
			formData.append('file', cvFile);
			formData.append('job_description', job.description);

			const res = await authFetch(`${API_BASE}/api/cv_tailor`, {
				method: 'POST',
				body: formData
			});

			if (res.ok) {
				const data = await res.json();
				tailoredResults[job.title] = data.tailored_cv;
			} else {
				const err = await res.json();
				alert('tailoring of CV is failed: ' + (err.detail || 'Unknown error'));
			}
		} catch (e) {
			console.error(e);
			alert('Error connecting to the server.');
		} finally {
			tailoringJobId = null;
		}
	}

	async function downloadPDF(text: string) {
		try {
			const res = await authFetch(`${API_BASE}/api/download_pdf`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ text: text })
			});

			if (res.ok) {
				const blob = await res.blob();
				const url = window.URL.createObjectURL(blob);
				const a = document.createElement('a');
				a.href = url;
				a.download = 'Tailored_CV.pdf';
				document.body.appendChild(a);
				a.click();

				window.URL.revokeObjectURL(url);
				document.body.removeChild(a);
			} else {
				alert('Failed to generate PDF');
			}
		} catch (e) {
			console.error(e);
			alert('Error downloading PDF');
		}
	}

	function formatMarkdown(text: string) {
		if (!text) return '';
		return text
			.replace(/\n/g, '<br>')
			.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
			.replace(/- (.*?)(<br>|$)/g, '• $1$2');
	}
</script>

<svelte:head>
	<title>Main Page</title>
</svelte:head>

<div class="page-container">
	<section class="input-section">
		<div class="glass-card">
			<h1>Job Recommender</h1>
			<p class="subtitle">Upload your CV and skills to find the jobs that fit you.</p>

			<div class="form-group">
				<label for="cv-upload">Upload CV (PDF/DOCX)</label>
				<div class="file-upload-wrapper">
					<input
						id="cv-upload"
						type="file"
						accept=".pdf,.docx"
						on:change={handleFileSelect}
						class="file-input"
					/>
					<div class="file-display">
						<span class="icon">📄</span>
						<span class="filename">{cvFile ? cvFile.name : 'Choose a file...'}</span>
					</div>
				</div>
			</div>

			<div class="form-group">
				<label for="cv">CV Content (for search)</label>
				<textarea id="cv" bind:value={cvText} placeholder="Paste your CV text here..." rows="4"
				></textarea>
			</div>

			<div class="form-group">
				<label for="job-title">Job Title</label>
				<input
					id="job-title"
					type="text"
					bind:value={query}
					placeholder="e.g. Software Engineer, Data Scientist"
				/>
			</div>

			<div class="form-group">
				<label for="skills">Skills (comma seperated)</label>
				<input
					id="skills"
					type="text"
					bind:value={skillsInput}
					placeholder="e.g. Python, React, SQL"
				/>
			</div>

			<div class="form-group">
				<label for="seniority">Seniority Level</label>
				<select id="seniority" bind:value={seniorityLevel}>
					<option value="All">All Levels</option>
					<option value="Intern">Intern/Trainee</option>
					<option value="Junior">Junior</option>
					<option value="Mid">Mid</option>
					<option value="Seniority">Senior</option>
				</select>
			</div>

			{#if error}
				<p class="error-msg">{error}</p>
			{/if}

			<button class="search-btn" on:click={handleSearch} disabled={loading}>
				{#if loading}
					<span class="loader"></span> Searching...
				{:else}
					Find Matches
				{/if}
			</button>
		</div>
	</section>

	<section class="results-section">
		{#if jobs.length > 0}
			<h2>Top Recommendations</h2>
			<div class="jobs-grid">
				{#each jobs as job}
					<div class="job-card">
						<div class="job-header">
							<h3>{job.title}</h3>
							<span
								class="score-badge"
								style="background: {job.match_score > 70 ? '#10b981' : '#f59e0b'}"
							>
								{job.match_score}% Match
							</span>
						</div>
						<p class="company">{job.company} * {job.location}</p>
						<p class="description">{job.description.slice(0, 150)}...</p>

						<div class="actions">
							<a href={job.link} target="_blank" class="apply-link">View Job</a>
							<button
								class="tailor-btn"
								on:click={() => handleTailorCV(job)}
								disabled={tailoringJobId === job.title}
							>
								{tailoringJobId === job.title ? 'Processing...' : 'Tailor CV'}
							</button>
						</div>
						{#if tailoredResults[job.title]}
							<div class="tailored-result">
								<div
									style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;"
								>
									<h4>AI Suggestions</h4>
									<button
										class="download-btn"
										on:click={() => downloadPDF(tailoredResults[job.title])}
										style="background:#10b981; color:white; border:none; padding:5px 10px; border-radius:4px; cursor:pointer;"
									>
										📥 Download PDF
									</button>
								</div>
								<div class="markdown-content">
									{@html formatMarkdown(tailoredResults[job.title])}
								</div>
							</div>
						{/if}
					</div>
				{/each}
			</div>
		{:else if !loading && !error}
			<div class="empty-state">
				<p>Jobs will appear here after you search.</p>
			</div>
		{/if}
	</section>
</div>

<style>
	.page-container {
		display: flex;
		min-height: 100vh;
		padding: 2rem;
		gap: 2rem;
		max-width: 1400px;
		margin: 0 auto;
	}

	.input-section {
		flex: 1;
		max-width: 450px;
	}

	.glass-card {
		background: rgb(255, 255, 255);
		backdrop-filter: blur(10px);
		border: 1px solid rgba(142, 141, 141, 0.611);
		padding: 2rem;
		border-radius: 16px;
		box-shadow: 0 4px 30px rgba(0, 0, 0, 0.1);
	}

	h1 {
		margin-top: 0;
		font-size: 1.8rem;
		background: linear-gradient(90deg, #0f21c0, #0f21c0);
		-webkit-background-clip: text;
		background-clip: text;
		-webkit-text-fill-color: transparent;
		color: transparent;
	}
	.subtitle {
		color: #4b4e51;
		margin-bottom: 1.5rem;
		font-size: 0.9rem;
	}

	.form-group {
		margin-bottom: 1.5rem;
	}
	label {
		display: block;
		margin-bottom: 0.5rem;
		font-weight: 500;
		color: #0b0b0b;
	}

	.file-upload-wrapper {
		position: relative;
		overflow: hidden;
		border: 2px dashed #092da5;
		border-radius: 8px;
		transition: border-color 0.2s;
		background: rgba(83, 82, 82, 0.788);
	}

	.file-upload-wrapper:hover {
		border-color: #2563eb;
		background: rgba(99, 102, 241, 0.1);
	}

	.file-input {
		position: absolute;
		top: 0;
		left: 0;
		width: 100%;
		height: 100%;
		opacity: 0;
		cursor: pointer;
	}

	.file-display {
		padding: 1rem;
		display: flex;
		align-items: center;
		gap: 0.5rem;
		color: #1a1a1a;
		justify-content: center;
	}
	.icon {
		font-size: 1.2rem;
	}

	textarea,
	input {
		width: 100%;
		background: rgba(188, 186, 186, 0.722);
		border: 1px solid #878c92;
		border-radius: 8px;
		padding: 0.75rem;
		color: rgb(17, 17, 17);
		font-family: inherit;
		box-sizing: border-box;
	}

	textarea:focus,
	input:focus {
		outline: 2px solid #171ac3;
		border-color: transparent;
	}

	select {
		width: 100%;
		background: rgba(255, 254, 254, 0.3);
		border: 1px solid #878c92;
		border-radius: 8px;
		padding: 0.75rem;
		color: rgb(17, 17, 17);
		font-family: inherit;
		box-sizing: border-box;
		cursor: pointer;
	}

	select:focus {
		outline: 2px solid #171ac3;
		border-color: transparent;
	}

	option {
		background-color: #1e293b;
		color: white;
	}

	.search-btn {
		width: 100%;
		padding: 1rem;
		background: #2563eb;
		color: white;
		border: none;
		border-radius: 8px;
		font-weight: 600;
		cursor: pointer;
		transition: background 0.2s;
	}

	.search-btn:hover {
		background: #1b12c9;
	}

	.search-btn:disabled {
		background: #e4e5e7;
		cursor: not-allowed;
	}

	.error-msg {
		color: #ef4444;
		font-size: 0.9rem;
		margin-bottom: 1rem;
	}

	.results-section {
		flex: 2;
		overflow-y: auto;
	}

	.jobs-grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
		gap: 1.5rem;
	}

	.job-card {
		background: rgb(255, 255, 255);
		border: 1px solid #7d7e81;
		border-radius: 12px;
		padding: 1.5rem;
		transition: transform 0.2s;
	}

	.job-card:hover {
		transform: translateY(-4px);
		border-color: #1114ca;
	}

	.job-header {
		display: flex;
		justify-content: space-between;
		align-items: start;
		margin-bottom: 0.5rem;
	}

	.job-header h3 {
		margin: 0;
		font-size: 1.1rem;
		color: #111213;
	}

	.score-badge {
		font-size: 0.75rem;
		padding: 0.25rem 0.5rem;
		border-radius: 99px;
		color: #020617;
		font-weight: 700;
	}

	.company {
		color: #7c848f91;
		font-size: 0.9rem;
		margin-bottom: 1rem;
	}

	.description {
		color: #cbd5e1;
		font-size: 0.9rem;
		line-height: 1.5;
		margin-bottom: 1.5rem;
	}

	.actions {
		display: flex;
		gap: 1rem;
	}

	.apply-link {
		flex: 1;
		text-align: center;
		padding: 0.5rem;
		border: 1px solid #072f9b;
		border-radius: 6px;
		color: blue;
		text-decoration: none;
		font-size: 0.9rem;
	}

	.apply-link:hover {
		background: #0a28bd;
	}

	.tailor-btn {
		flex: 1;
		background: rgba(24, 28, 245, 0.2);
		color: #1d30d7;
		border: 1px solid rgba(24, 28, 245, 0.3);
		border-radius: 6px;
		cursor: pointer;
		font-weight: 600;
	}

	.tailor-btn:hover {
		background: rgba(24, 28, 245, 0.3);
	}

	.empty-state {
		height: 100%;
		display: flex;
		align-items: center;
		justify-content: center;
		color: #64748b;
		border: 2px dashed #334155;
		border-radius: 16px;
	}

	@media (max-width: 768px) {
		.page-container {
			flex-direction: column;
		}
		.input-section {
			max-width: 100%;
		}
	}
</style>
