<script lang="ts">
	import { onMount } from 'svelte';
	import AppShell from '$lib/components/AppShell.svelte';
	import { API_BASE, getATSScore, getRecommendations, type Job } from '$lib/api';
	import {
		createApplication,
		getApplications,
		updateApplicationStatus
	} from '$lib/api/applications';
	import { authFetch } from '$lib/auth';
	import { cvWorkspace } from '$lib/stores/cv-workspace';
	import type { Application, ApplicationStatus } from '$lib/types/application';

	type JobFeedback = {
		message: string;
		tone: 'success' | 'error';
	};

	let cvText = '';
	let skillsInput = '';
	let seniorityLevel = 'All';
	let query = '';
	let jobs: Job[] = [];
	let loading = false;
	let parsingCv = false;
	let error = '';
	let cvFile: File | null = null;
	let tailoringJobId: string | null = null;
	let tailoredResults: Record<string, string> = {};
	let savingJobKey: string | null = null;
	let savedJobKeys: string[] = [];
	let trackedApplicationLookup: Record<string, Application> = {};
	let jobSaveFeedback: Record<string, JobFeedback> = {};
	let applyPromptJob: Job | null = null;
	let sharedSourceName = '';
	let fullName = '';
	let hydrated = false;
	let selectedCountries: string[] = ['pl'];
	let atsJobKey: string | null = null;
	let atsResult: {
		score: number;
		missing_keywords: string[];
		formatting_issues: string[];
		suggestions: string[];
	} | null = null;
	let atsLoading = false;

	onMount(() => {
		const unsubscribe = cvWorkspace.subscribe((state) => {
			if (cvFile && state.sourceName && state.sourceName !== cvFile.name) {
				cvFile = null;
			}

			if (!state.cvText.trim() && !state.sourceName) {
				cvFile = null;
			}

			cvText = state.cvText;
			skillsInput = state.skills.join(', ');
			sharedSourceName = state.sourceName;
			fullName = state.fullName;
		});

		void loadTrackedApplications();
		hydrated = true;

		return unsubscribe;
	});

	function parseSkillsInput(value: string) {
		return value
			.split(',')
			.map((skill) => skill.trim())
			.filter((skill, index, skills) => skill.length > 0 && skills.indexOf(skill) === index);
	}

	$: if (hydrated) {
		cvWorkspace.patch({
			cvText,
			skills: parseSkillsInput(skillsInput),
			sourceName: sharedSourceName,
			fullName
		});
	}

	$: currentCvName = cvFile?.name || sharedSourceName || 'No CV file attached yet';
	$: currentCvDescription = parsingCv
		? 'Reading your uploaded CV now.'
		: cvFile
			? 'Your uploaded file is ready for search and tailoring.'
			: sharedSourceName
				? 'This CV was synced from the builder and is ready for search and tailoring.'
				: 'Attach a PDF or DOCX to unlock CV extraction and tailored rewrite suggestions.';
	$: promptTrackedApplication = applyPromptJob ? getTrackedApplication(applyPromptJob) : null;

	function normalizeTrackerValue(value: string | undefined) {
		return (value ?? '').trim().toLowerCase();
	}

	function buildTrackedKey(jobTitle: string, company: string, jobUrl?: string) {
		const normalizedTitle = normalizeTrackerValue(jobTitle);
		const normalizedCompany = normalizeTrackerValue(company);
		const normalizedUrl = normalizeTrackerValue(jobUrl);

		return normalizedUrl
			? `${normalizedCompany}::${normalizedTitle}::${normalizedUrl}`
			: `${normalizedCompany}::${normalizedTitle}`;
	}

	function getApplicationLookupKeys(application: Application) {
		const keys = [buildTrackedKey(application.job_title, application.company)];

		if (application.job_url) {
			keys.unshift(
				buildTrackedKey(application.job_title, application.company, application.job_url)
			);
		}

		return keys;
	}

	function syncTrackedApplications(applications: Application[]) {
		const nextLookup: Record<string, Application> = {};
		const nextKeys: string[] = [];

		for (const application of applications) {
			for (const key of getApplicationLookupKeys(application)) {
				nextLookup[key] = application;
				if (!nextKeys.includes(key)) {
					nextKeys.push(key);
				}
			}
		}

		trackedApplicationLookup = nextLookup;
		savedJobKeys = nextKeys;
	}

	async function loadTrackedApplications() {
		try {
			syncTrackedApplications(await getApplications());
		} catch (err) {
			console.error('Could not load tracked applications.', err);
		}
	}

	async function handleFileSelect(event: Event) {
		const target = event.target as HTMLInputElement;
		if (target.files && target.files.length > 0) {
			cvFile = target.files[0];

			const formData = new FormData();
			formData.append('file', cvFile);

			parsingCv = true;
			error = '';

			try {
				const res = await authFetch(`${API_BASE}/api/parse_cv`, {
					method: 'POST',
					body: formData
				});

				if (res.ok) {
					const data = await res.json();
					cvText = data.text;
					skillsInput = data.skills && data.skills.length > 0 ? data.skills.join(', ') : '';
					sharedSourceName = cvFile.name;
				} else {
					error = 'Failed to read file text.';
				}
			} catch (err) {
				console.error(err);
				error = 'Error parsing file.';
			} finally {
				parsingCv = false;
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

		const skillsArray = parseSkillsInput(skillsInput);
		const countryParam = selectedCountries.join(',');
		try {
			const response = await getRecommendations(cvText, query, skillsArray, seniorityLevel, countryParam);
			jobs = response.jobs;
		} catch (err) {
			console.error(err);
			error = 'Failed to fetch jobs. Please check the backend connection.';
		} finally {
			loading = false;
		}
	}

	async function handleTailorCV(job: Job) {
		if (!cvText.trim()) {
			alert('Please upload or paste CV content before tailoring.');
			return;
		}

		tailoringJobId = job.title;

		try {
			const formData = new FormData();
			formData.append('cv_text', cvText);
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
				body: JSON.stringify({ text, name: fullName })
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

	function safeExternalUrl(link: string) {
		try {
			const url = new URL(link);
			return url.protocol === 'http:' || url.protocol === 'https:' ? url.toString() : '#';
		} catch {
			return '#';
		}
	}

	function getJobKey(job: Job) {
		return `${job.source}:${job.company}:${job.title}:${job.link}`;
	}

	function getTrackedApplication(job: Job) {
		const safeJobUrl = safeExternalUrl(job.link);

		return (
			trackedApplicationLookup[
				buildTrackedKey(job.title, job.company, safeJobUrl === '#' ? undefined : safeJobUrl)
			] ?? trackedApplicationLookup[buildTrackedKey(job.title, job.company)]
		);
	}

	function getSaveButtonLabel(job: Job) {
		const trackedApplication = getTrackedApplication(job);
		if (!trackedApplication) {
			return 'Save to tracker';
		}

		if (trackedApplication.status === 'applied') {
			return 'Applied';
		}

		return 'In tracker';
	}

	function upsertTrackedApplication(application: Application) {
		const nextLookup = { ...trackedApplicationLookup };
		const nextKeys = [...savedJobKeys];

		for (const key of getApplicationLookupKeys(application)) {
			nextLookup[key] = application;
			if (!nextKeys.includes(key)) {
				nextKeys.push(key);
			}
		}

		trackedApplicationLookup = nextLookup;
		savedJobKeys = nextKeys;
	}

	async function syncJobWithTracker(
		job: Job,
		targetStatus: ApplicationStatus,
		successMessage: string
	) {
		const jobKey = getJobKey(job);
		const safeJobUrl = safeExternalUrl(job.link);
		const existingApplication = getTrackedApplication(job);

		savingJobKey = jobKey;
		jobSaveFeedback = Object.fromEntries(
			Object.entries(jobSaveFeedback).filter(([existingKey]) => existingKey !== jobKey)
		);

		try {
			if (existingApplication) {
				if (existingApplication.status === targetStatus) {
					jobSaveFeedback = {
						...jobSaveFeedback,
						[jobKey]: {
							message: `Already marked as ${targetStatus} in your tracker.`,
							tone: 'success'
						}
					};
					return true;
				}

				const updatedApplication = await updateApplicationStatus(
					existingApplication.id,
					targetStatus
				);
				upsertTrackedApplication(updatedApplication);
			} else {
				const createdApplication = await createApplication({
					job_title: job.title,
					company: job.company,
					job_url: safeJobUrl === '#' ? undefined : safeJobUrl,
					status: targetStatus
				});
				upsertTrackedApplication(createdApplication);
			}

			jobSaveFeedback = {
				...jobSaveFeedback,
				[jobKey]: { message: successMessage, tone: 'success' }
			};
			return true;
		} catch (err) {
			console.error(err);
			jobSaveFeedback = {
				...jobSaveFeedback,
				[jobKey]: {
					message:
						targetStatus === 'applied'
							? 'Could not mark this role as applied right now.'
							: 'Could not save this role right now.',
					tone: 'error'
				}
			};
			return false;
		} finally {
			savingJobKey = null;
		}
	}

	async function saveJobToTracker(job: Job) {
		await syncJobWithTracker(job, 'saved', 'Saved to your tracker.');
	}

	function openApplyPrompt(job: Job) {
		const safeJobUrl = safeExternalUrl(job.link);

		if (safeJobUrl === '#') {
			jobSaveFeedback = {
				...jobSaveFeedback,
				[getJobKey(job)]: {
					message: 'This job link looks invalid, so it could not be opened.',
					tone: 'error'
				}
			};
			return;
		}

		window.open(safeJobUrl, '_blank');
		applyPromptJob = job;
	}

	function closeApplyPrompt() {
		applyPromptJob = null;
	}

	async function confirmAppliedFromPrompt() {
		if (!applyPromptJob) {
			return;
		}

		const currentJob = applyPromptJob;
		const success = await syncJobWithTracker(
			currentJob,
			'applied',
			'Added to your tracker as applied.'
		);

		if (success) {
			closeApplyPrompt();
		}
	}

	async function handleATSScore(job: Job) {
		atsJobKey = getJobKey(job);     
		atsResult = null;
		atsLoading = true;
		try {
			atsResult = await getATSScore(cvText, job.description);
		} catch(err) {
			console.error(err);
			atsResult = {
				score: 0,
				missing_keywords: [],
				formatting_issues: [],
				suggestions: ['Could not retrieve ATS analysis.']
			};
		} finally {
			atsLoading = false;
		}
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
			<h3>{currentCvName}</h3>
			<p>{currentCvDescription}</p>
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
							<span class="filename">{parsingCv ? 'Reading CV...' : currentCvName}</span>
						</div>
					</div>
					{#if sharedSourceName && !cvFile}
						<p class="sync-note">
							Synced from the CV Builder. Upload a new file here only if you want to replace it.
						</p>
					{/if}
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
						<option value="Senior">Senior</option>
					</select>
				</div>

				<div class="form-group">
					<label for="countries">Countries</label>
					<select 
						id="countries"
						multiple
						bind:value={selectedCountries}
						class="multi-country"
						>
						        <option value="pl">Poland</option>
        						<option value="de">Germany</option>
        						<option value="fr">France</option>
        						<option value="gb">United Kingdom</option>
        						<option value="us">United States</option>
        						<option value="nl">Netherlands</option>
        						<option value="se">Sweden</option>
        						<option value="ca">Canada</option>
								<option value="it">Italy</option>
						</select>			
						<p class="hint">Hold Ctrl (Cmd) to select multiple countries.</p>
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
					{#each jobs as job (getJobKey(job))}
						{@const jobKey = getJobKey(job)}
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
								<button
									type="button"
									class="apply-link"
									on:click={() => openApplyPrompt(job)}
									disabled={savingJobKey === jobKey}
								>
									Open job and log application
								</button>
								<button
									class="tailor-btn"
									type="button"
									on:click={() => handleATSScore(job)}  
									disabled={atsLoading && atsJobKey == jobKey}
								>
									{atsLoading && atsJobKey == jobKey ? 'Analysing...' : 'Check ATS Score'}
								</button>
								<button
									class="tailor-btn"
									type="button"
									on:click={() => handleTailorCV(job)}
									disabled={tailoringJobId === job.title}
								>
									{tailoringJobId === job.title ? 'Processing...' : 'Tailor CV'}
								</button>
								<button
									class="save-btn"
									type="button"
									on:click={() => saveJobToTracker(job)}
									disabled={savingJobKey === jobKey || savedJobKeys.includes(jobKey)}
								>
									{#if savingJobKey === jobKey}
										Saving...
									{:else}
										{getSaveButtonLabel(job)}
									{/if}
								</button>
							</div>

							{#if jobSaveFeedback[jobKey]}
								<p class={`job-feedback ${jobSaveFeedback[jobKey].tone}`}>
									{jobSaveFeedback[jobKey].message}
								</p>
							{/if}

							{#if tailoredResults[job.title]}
								<div class="tailored-result">
									<div class="tailored-header">
										<h4>Tailored CV</h4>
										<button
											class="download-btn"
											on:click={() => downloadPDF(tailoredResults[job.title])}
										>
											Download PDF
										</button>
									</div>
									<div class="markdown-content">{tailoredResults[job.title]}</div>
								</div>
							{/if}
							{#if atsResult && atsJobKey === jobKey}
								<div class="tailored-result">
									<h4>ATS Analysis</h4>
									<div class="ats-score">
										<strong>Score: {atsResult.score}/100</strong>
									</div>
									{#if atsResult.missing_keywords?.length}
										<p><strong>Missing Keywords:</strong> {atsResult.missing_keywords.join(', ')}</p>
									{/if}
									{#if atsResult.formatting_issues?.length}
										<p><strong>Formatting Issues:</strong></p>
										<ul>
											{#each atsResult.formatting_issues as issue}
												<li>{issue}</li>
											{/each}
										</ul>
									{/if}
									{#if atsResult.suggestions?.length}
										<p><strong>Suggestions:</strong></p>
										<ul>
											{#each atsResult.suggestions as suggestion}
												<li>{suggestion}</li>
											{/each}
										</ul>
									{/if}
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

{#if applyPromptJob}
	<div class="apply-modal-backdrop" role="presentation">
		<div
			class="apply-modal"
			role="dialog"
			aria-modal="true"
			aria-labelledby="apply-modal-title"
			tabindex="-1"
		>
			<p class="guide-kicker">Tracker update</p>
			<h3 id="apply-modal-title">Did you apply for {applyPromptJob.title}?</h3>
			<p class="apply-modal-copy">
				{#if promptTrackedApplication}
					This role is already in your tracker as <strong>{promptTrackedApplication.status}</strong
					>. If you applied, we&apos;ll update it to <strong>applied</strong>.
				{:else}
					If yes, we&apos;ll add it to your tracker as <strong>applied</strong>. You can change the
					status later from the Tracker page.
				{/if}
			</p>

			<div class="apply-modal-actions">
				<button type="button" class="modal-secondary" on:click={closeApplyPrompt}> Not yet </button>
				<button
					type="button"
					class="modal-primary"
					on:click={confirmAppliedFromPrompt}
					disabled={savingJobKey === getJobKey(applyPromptJob)}
				>
					{savingJobKey === getJobKey(applyPromptJob) ? 'Updating...' : 'Yes, mark as applied'}
				</button>
			</div>
		</div>
	</div>
{/if}

<style>
	.ats-score {
		font-size: 1.2rem;
		color: #0f6b53;
		margin: 0.5rem 0;
	}
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

	.multi-country{
		min-height: 100px;
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

	.sync-note {
		margin: 0.65rem 0 0;
		color: #5b7288;
		font-size: 0.9rem;
		line-height: 1.5;
	}

	.search-btn {
		width: 100%;
		padding: 1rem;
		border: none;
		border-radius: 1rem;
		background: linear-gradient(135deg, #0e11ee);
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
	.tailor-btn,
	.save-btn {
		padding: 0.75rem 1.25rem;
		border-radius: 10px;
		font-weight: 600;
	}

	.apply-link {
		background: #2563eb;
		color: white;
		border: none;
		cursor: pointer;
	}

	.tailor-btn {
		border: 1px solid #8fb0d4;
		background: white;
		color: #1a4f90;
		cursor: pointer;
	}

	.save-btn {
		border: 1px solid rgba(15, 138, 103, 0.25);
		background: rgba(231, 247, 238, 0.96);
		color: #0f6b53;
		cursor: pointer;
	}

	.tailor-btn:disabled,
	.save-btn:disabled {
		opacity: 0.7;
		cursor: not-allowed;
	}

	.job-feedback {
		margin: 0.9rem 0 0;
		font-size: 0.92rem;
		font-weight: 600;
	}

	.job-feedback.success {
		color: #0f766e;
	}

	.job-feedback.error {
		color: #b42318;
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
		white-space: pre-wrap;
		word-break: break-word;
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

	.apply-modal-backdrop {
		position: fixed;
		inset: 0;
		display: grid;
		place-items: center;
		padding: 1.5rem;
		background: rgba(12, 22, 38, 0.45);
		backdrop-filter: blur(6px);
		z-index: 120;
	}

	.apply-modal {
		width: min(100%, 30rem);
		padding: 1.5rem;
		border-radius: 1.5rem;
		border: 1px solid rgba(138, 160, 185, 0.28);
		background: rgba(252, 253, 255, 0.98);
		box-shadow: 0 30px 60px rgba(17, 33, 56, 0.2);
	}

	.apply-modal h3 {
		margin: 0 0 0.75rem;
		color: #16324f;
	}

	.apply-modal-copy {
		margin: 0;
		line-height: 1.65;
		color: #52687f;
	}

	.apply-modal-actions {
		display: flex;
		justify-content: flex-end;
		gap: 0.85rem;
		margin-top: 1.5rem;
		flex-wrap: wrap;
	}

	.modal-primary,
	.modal-secondary {
		padding: 0.8rem 1.1rem;
		border-radius: 999px;
		font-weight: 700;
		cursor: pointer;
	}

	.modal-primary {
		border: none;
		background: linear-gradient(135deg, #143b6b, #2563eb);
		color: #f8fbff;
	}

	.modal-secondary {
		border: 1px solid rgba(138, 160, 185, 0.4);
		background: #ffffff;
		color: #23405d;
	}

	.modal-primary:disabled {
		opacity: 0.7;
		cursor: not-allowed;
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

		.apply-modal-actions {
			flex-direction: column-reverse;
			align-items: stretch;
		}
	}
</style>
