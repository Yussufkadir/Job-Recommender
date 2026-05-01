<script lang="ts">
	import AppShell from '$lib/components/AppShell.svelte';
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
					skillsInput = data.skills && data.skills.length > 0 ? data.skills.join(', ') : '';
				} else {
					cvText = '';
					alert('Failed to read file text.');
				}
			} catch (err) {
				console.error(err);
				cvText = '';
				alert('Error parsing file.');
			}
		}
	}

	async function handleSearch() {
		if (!cvText && !skillsInput) {
			error = 'Please add CV content or extracted skills before searching.';
			return;
		}

		if (!query) {
			error = 'Please enter a job title to find relevant roles.';
			return;
		}

		loading = true;
		error = '';
		jobs = [];

		const skillsArray = skillsInput
			.split(',')
			.map((skill) => skill.trim())
			.filter((skill) => skill.length > 0);

		try {
			const response = await getRecommendations(cvText, query, skillsArray, seniorityLevel);
			jobs = response.jobs;
		} catch (err) {
			console.error(err);
			error = 'Failed to fetch jobs. Please check the backend connection.';
		} finally {
			loading = false;
		}
	}

	async function handleTailorCV(job: Job) {
		if (!cvFile) {
			alert('Please upload a CV file (PDF/DOCX) before tailoring.');
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
				alert(`CV tailoring failed: ${err.detail || 'Unknown error'}`);
			}
		} catch (err) {
			console.error(err);
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
				body: JSON.stringify({ text })
			});

			if (res.ok) {
				const blob = await res.blob();
				const url = window.URL.createObjectURL(blob);
				const link = document.createElement('a');
				link.href = url;
				link.download = 'Tailored_CV.pdf';
				document.body.appendChild(link);
				link.click();
				window.URL.revokeObjectURL(url);
				document.body.removeChild(link);
			} else {
				alert('Failed to generate PDF.');
			}
		} catch (err) {
			console.error(err);
			alert('Error downloading PDF.');
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
	<title>Job Search | Job Recommender</title>
</svelte:head>

<AppShell
	eyebrow="Search Workspace"
	heading="Search, compare, and tailor roles without leaving the flow."
	subheading="This tab is now the dedicated workspace for recommendations, CV parsing, and tailored application support."
>
	<section class="guide-grid">
		<article class="guide-card">
			<p class="guide-kicker">How to use it</p>
			<h3>Bring your CV, target the right role, and refine from there.</h3>
			<p>
				Upload a file if you have one, paste CV text if you do not, then define the role and skills
				you want the recommender to optimize for.
			</p>
		</article>

		<article class="guide-card file-status">
			<p class="guide-kicker">Current context</p>
			<h3>{cvFile ? cvFile.name : 'No CV file attached yet'}</h3>
			<p>
				{cvFile
					? 'Your uploaded file is ready for parsing and tailoring.'
					: 'Attach a PDF or DOCX to unlock CV extraction and tailored rewrite suggestions.'}
			</p>
		</article>
	</section>

	<div class="page-container">
		<section class="input-section">
			<div class="glass-card">
				<h2>Recommendation inputs</h2>
				<p class="subtitle">Set up the search once, then iterate until the results feel sharp.</p>

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
							<span class="icon">CV</span>
							<span class="filename">{cvFile ? cvFile.name : 'Choose a file...'}</span>
						</div>
					</div>
				</div>

				<div class="form-group">
					<label for="cv">CV Content (for search)</label>
					<textarea id="cv" bind:value={cvText} placeholder="Paste your CV text here..." rows="6"
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
					<label for="skills">Skills (comma separated)</label>
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
			<div class="results-header">
				<div>
					<p class="guide-kicker">Results</p>
					<h2>Recommended roles</h2>
				</div>
				{#if jobs.length > 0}
					<span class="results-count">{jobs.length} matches</span>
				{/if}
			</div>

			{#if jobs.length > 0}
				<div class="jobs-grid">
					{#each jobs as job}
						<div class="job-card">
							<div class="job-header">
								<div>
									<h3>{job.title}</h3>
									<p class="company">{job.company} • {job.location}</p>
								</div>
								<span
									class="score-badge"
									style={`background: ${job.match_score > 70 ? '#e7f7ee' : '#fff4df'}; color: ${job.match_score > 70 ? '#0f6b53' : '#9a6700'}`}
								>
									{job.match_score}% Match
								</span>
							</div>
							<p class="description">{job.description.slice(0, 180)}...</p>

							<div class="actions">
								<a href={job.link} target="_blank" rel="noreferrer" class="apply-link">View Job</a>
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
									<div class="tailored-header">
										<h4>AI Suggestions</h4>
										<button
											class="download-btn"
											on:click={() => downloadPDF(tailoredResults[job.title])}
										>
											Download PDF
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
					<h3>Your matches will appear here.</h3>
					<p>Once you run a search, this panel becomes the place to compare and tailor results.</p>
				</div>
			{/if}
		</section>
	</div>
</AppShell>

<style>
	.guide-grid {
		display: grid;
		grid-template-columns: minmax(0, 1.2fr) minmax(0, 0.8fr);
		gap: 1rem;
		margin-bottom: 1.25rem;
	}

	.guide-card {
		padding: 1.35rem;
		border-radius: 1.6rem;
		border: 1px solid rgba(137, 159, 182, 0.26);
		background: rgba(250, 252, 255, 0.86);
		box-shadow: 0 22px 42px rgba(29, 48, 78, 0.08);
	}

	.guide-kicker {
		margin: 0 0 0.45rem;
		text-transform: uppercase;
		letter-spacing: 0.12em;
		font-size: 0.76rem;
		font-weight: 700;
		color: #5d7898;
	}

	.guide-card h3,
	.results-header h2,
	.glass-card h2,
	.job-card h3,
	.tailored-result h4,
	.empty-state h3 {
		margin: 0;
		color: #16324f;
	}

	.guide-card h3 {
		margin-bottom: 0.7rem;
		font-size: 1.5rem;
	}

	.guide-card p {
		margin: 0;
		line-height: 1.65;
		color: #54697f;
	}

	.page-container {
		display: flex;
		gap: 2rem;
		align-items: flex-start;
	}

	.input-section {
		flex: 1;
		max-width: 450px;
	}

	.glass-card {
		background: rgba(250, 252, 255, 0.92);
		backdrop-filter: blur(18px);
		border: 1px solid rgba(138, 160, 185, 0.28);
		padding: 2rem;
		border-radius: 1.6rem;
		box-shadow: 0 26px 44px rgba(31, 51, 84, 0.08);
	}

	.glass-card h2 {
		font-size: 1.6rem;
		margin-bottom: 0.4rem;
	}

	.subtitle {
		color: #5c7087;
		margin-bottom: 1.6rem;
		line-height: 1.6;
	}

	.form-group {
		margin-bottom: 1.5rem;
	}

	label {
		display: block;
		margin-bottom: 0.5rem;
		font-weight: 600;
		color: #25415e;
	}

	input,
	textarea,
	select {
		width: 100%;
		padding: 0.9rem 1rem;
		border: 1px solid #d6e1ec;
		border-radius: 1rem;
		font-size: 0.95rem;
		box-sizing: border-box;
		background: rgba(255, 255, 255, 0.92);
		color: #173557;
	}

	textarea {
		resize: vertical;
		min-height: 100px;
	}

	.file-upload-wrapper {
		position: relative;
	}

	.file-input {
		position: absolute;
		inset: 0;
		opacity: 0;
		cursor: pointer;
	}

	.file-display {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		padding: 1rem;
		border: 2px dashed #c8d9ea;
		border-radius: 1rem;
		background: #f6faff;
		cursor: pointer;
	}

	.icon {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		width: 2.5rem;
		height: 2.5rem;
		border-radius: 0.85rem;
		font-size: 0.8rem;
		font-weight: 800;
		letter-spacing: 0.08em;
		color: #f7fbff;
		background: linear-gradient(135deg, #143b6b, #2563eb);
	}

	.filename {
		color: #52687f;
	}

	.search-btn {
		width: 100%;
		padding: 1rem;
		border: none;
		border-radius: 1rem;
		background: linear-gradient(135deg, #143b6b, #2563eb);
		color: white;
		font-size: 1rem;
		font-weight: 700;
		cursor: pointer;
		transition:
			transform 0.2s,
			box-shadow 0.2s;
	}

	.search-btn:hover:not(:disabled) {
		transform: translateY(-2px);
		box-shadow: 0 18px 26px rgba(20, 59, 107, 0.22);
	}

	.search-btn:disabled {
		opacity: 0.7;
		cursor: not-allowed;
	}

	.loader {
		display: inline-block;
		width: 1rem;
		height: 1rem;
		border: 2px solid rgba(255, 255, 255, 0.3);
		border-top: 2px solid white;
		border-radius: 50%;
		animation: spin 0.8s linear infinite;
		margin-right: 0.5rem;
	}

	@keyframes spin {
		to {
			transform: rotate(360deg);
		}
	}

	.error-msg {
		color: #b42318;
		margin-bottom: 1rem;
	}

	.results-section {
		flex: 2;
	}

	.results-header {
		display: flex;
		align-items: flex-end;
		justify-content: space-between;
		gap: 1rem;
		margin-bottom: 1rem;
	}

	.results-count {
		padding: 0.55rem 0.85rem;
		border-radius: 999px;
		font-weight: 700;
		color: #234d82;
		background: rgba(228, 238, 248, 0.95);
	}

	.jobs-grid {
		display: grid;
		gap: 1.5rem;
	}

	.job-card {
		background: rgba(250, 252, 255, 0.92);
		border: 1px solid rgba(138, 160, 185, 0.26);
		border-radius: 1.45rem;
		padding: 1.5rem;
		box-shadow: 0 22px 40px rgba(31, 51, 84, 0.08);
	}

	.job-header {
		display: flex;
		justify-content: space-between;
		gap: 1rem;
		align-items: flex-start;
	}

	.score-badge {
		padding: 0.5rem 0.85rem;
		border-radius: 999px;
		font-size: 0.85rem;
		font-weight: 700;
		white-space: nowrap;
	}

	.company {
		color: #2b5c99;
		font-weight: 600;
		margin: 0.4rem 0 1rem 0;
	}

	.description {
		color: #586f86;
		line-height: 1.6;
		margin-bottom: 1.5rem;
	}

	.actions {
		display: flex;
		gap: 1rem;
		flex-wrap: wrap;
	}

	.apply-link,
	.tailor-btn {
		padding: 0.75rem 1.25rem;
		border-radius: 10px;
		font-weight: 600;
	}

	.apply-link {
		background: #2563eb;
		color: white;
		text-decoration: none;
		border: none;
	}

	.tailor-btn {
		border: 1px solid #8fb0d4;
		background: white;
		color: #1a4f90;
		cursor: pointer;
	}

	.tailor-btn:disabled {
		opacity: 0.7;
		cursor: not-allowed;
	}

	.tailored-result {
		margin-top: 1.5rem;
		padding: 1rem;
		background: #f6fbff;
		border-radius: 1rem;
		border-left: 4px solid #2563eb;
	}

	.markdown-content {
		line-height: 1.6;
		color: #374f68;
	}

	.tailored-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		gap: 1rem;
		margin-bottom: 0.9rem;
	}

	.download-btn {
		background: #0f8a67;
		color: white;
		border: none;
		padding: 0.6rem 0.95rem;
		border-radius: 999px;
		cursor: pointer;
		font-weight: 700;
	}

	.empty-state {
		padding: 2rem;
		text-align: center;
		color: #5c7087;
		border: 1px dashed rgba(138, 160, 185, 0.4);
		border-radius: 1.45rem;
		background: rgba(250, 252, 255, 0.7);
	}

	.empty-state h3 {
		margin-bottom: 0.6rem;
	}

	.empty-state p {
		margin: 0;
		line-height: 1.6;
	}

	@media (max-width: 1024px) {
		.guide-grid {
			grid-template-columns: 1fr;
		}

		.page-container {
			flex-direction: column;
		}

		.input-section {
			max-width: none;
			width: 100%;
		}
	}

	@media (max-width: 768px) {
		.glass-card {
			padding: 1.5rem;
		}

		.results-header,
		.job-header,
		.actions {
			flex-direction: column;
			align-items: stretch;
		}

		.score-badge,
		.results-count {
			align-self: flex-start;
		}

		.tailored-header {
			flex-direction: column;
			align-items: stretch;
		}
	}
</style>
