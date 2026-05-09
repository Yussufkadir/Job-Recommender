<script lang="ts">
	import { browser } from '$app/environment';
	import { onMount } from 'svelte';
	import AppShell from '$lib/components/AppShell.svelte';
	import { API_BASE } from '$lib/api';
	import { authFetch } from '$lib/auth';

	const STORAGE_KEY = 'cv-builder-draft';
	const FILE_NAME_KEY = 'cv-builder-file-name';
	const FULL_NAME_KEY = 'cv-builder-full-name';
	const defaultFileName = 'my_cv';

	let cvText = '';
	let fileName = defaultFileName;
	let fullName = '';
	let documentUploadInput: HTMLInputElement | null = null;
	let hydrated = false;
	let notice = '';
	let noticeTone: 'neutral' | 'error' = 'neutral';
	let importingDocument = false;
	let generatingPdf = false;
	let importedSourceName = '';
	let extractedText = '';

	function readStoredValue(key: string) {
		if (!browser) {
			return null;
		}

		const sessionValue = sessionStorage.getItem(key);
		if (sessionValue !== null) {
			localStorage.removeItem(key);
			return sessionValue;
		}

		const legacyValue = localStorage.getItem(key);
		if (legacyValue !== null) {
			sessionStorage.setItem(key, legacyValue);
			localStorage.removeItem(key);
			return legacyValue;
		}

		return null;
	}

	function persistDraftValue(key: string, value: string) {
		sessionStorage.setItem(key, value);
		localStorage.removeItem(key);
	}

	onMount(() => {
		if (!browser) {
			return;
		}

		const savedDraft = readStoredValue(STORAGE_KEY);
		const savedFileName = readStoredValue(FILE_NAME_KEY);
		const savedFullName = readStoredValue(FULL_NAME_KEY);

		if (savedDraft) {
			cvText = savedDraft;
		}

		if (savedFileName) {
			fileName = savedFileName;
		}

		if (savedFullName) {
			fullName = savedFullName;
		}

		hydrated = true;
	});

	$: lineCount = cvText.split('\n').length;
	$: wordCount = cvText.trim() ? cvText.trim().split(/\s+/).length : 0;
	$: if (browser && hydrated) {
		persistDraftValue(STORAGE_KEY, cvText);
		persistDraftValue(FILE_NAME_KEY, fileName);
		persistDraftValue(FULL_NAME_KEY, fullName);
	}

	function normalizeFileName(name: string, extension = 'txt') {
		const trimmed = name.trim() || 'my_cv';
		const withoutExtension = trimmed.replace(/\.[a-z0-9]+$/i, '');
		const safeBase = withoutExtension
			.replace(/[^a-z0-9._-]+/gi, '-')
			.replace(/-+/g, '-')
			.replace(/^-|-$/g, '');

		return `${safeBase || 'my_cv'}.${extension}`;
	}

	function setNotice(message: string, tone: 'neutral' | 'error' = 'neutral') {
		notice = message;
		noticeTone = tone;
	}

	async function getErrorMessage(response: Response, fallback: string) {
		try {
			const data = await response.json();
			if (typeof data?.detail === 'string') {
				return data.detail;
			}
		} catch (error) {
			console.error(error);
		}

		return fallback;
	}

	async function downloadPdf() {
		if (!cvText.trim()) {
			setNotice('Please add some CV content first.', 'error');
			return;
		}

		if (!fullName.trim()) {
			setNotice('Enter your full name so it appears first in the generated PDF.', 'error');
			return;
		}

		generatingPdf = true;
		setNotice('Generating your CV as PDF...');

		try {
			const response = await authFetch(`${API_BASE}/api/download_pdf`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					text: cvText,
					name: fullName.trim()
				})
			});

			if (!response.ok) {
				const errorMsg = await getErrorMessage(response, 'Could not generate PDF.');
				setNotice(errorMsg, 'error');
				return;
			}

			const blob = await response.blob();
			const url = URL.createObjectURL(blob);
			const link = document.createElement('a');

			link.href = url;
			link.download = normalizeFileName(fileName, 'pdf');
			document.body.appendChild(link);
			link.click();
			document.body.removeChild(link);
			URL.revokeObjectURL(url);

			setNotice('Downloaded your CV as a PDF!');
		} catch (error) {
			console.error(error);
			setNotice('Could not reach the server.', 'error');
		} finally {
			generatingPdf = false;
		}
	}

	async function handleDocumentImport(event: Event) {
		const target = event.currentTarget as HTMLInputElement;
		const file = target.files?.[0];

		if (!file) {
			return;
		}

		importingDocument = true;
		setNotice(`Extracting text from ${file.name}...`);

		try {
			const formData = new FormData();
			formData.append('file', file);

			const response = await authFetch(`${API_BASE}/api/parse_cv`, {
				method: 'POST',
				body: formData
			});

			if (!response.ok) {
				setNotice(
					await getErrorMessage(response, 'Could not extract text from that file.'),
					'error'
				);
				return;
			}

			const data = (await response.json()) as {
				text?: string;
				skills?: string[];
			};

			cvText = data.text || '';
			fileName = normalizeFileName(file.name, 'txt');
			importedSourceName = file.name;
			extractedText = data.text || '';
			
			setNotice(
				`Imported text from ${file.name}. Add your full name above so it stays the first parsed line in the exported PDF.`
			);
		} catch (error) {
			console.error(error);
			setNotice('Could not reach the server for CV parsing.', 'error');
		} finally {
			importingDocument = false;
			target.value = '';
		}
	}

	function clearEditor() {
		cvText = '';
		fileName = defaultFileName;
		fullName = '';
		importedSourceName = '';
		extractedText = '';
		setNotice('Cleared the editor.');
	}

	function copyText() {
		if (!browser || !navigator.clipboard) {
			setNotice('Clipboard access is not available.', 'error');
			return;
		}

		navigator.clipboard.writeText(cvText).then(() => {
			setNotice('Copied CV text to clipboard!');
			setTimeout(() => setNotice(''), 2000);
		}).catch(() => {
			setNotice('Copy failed. You can still download as PDF.', 'error');
		});
	}
</script>

<svelte:head>
	<title>CV Builder | Job Recommender</title>
</svelte:head>

<AppShell
	eyebrow="CV Builder"
	heading="Create your ATS-friendly CV and download as PDF"
	subheading="Import an existing CV, edit the content, and download a clean, machine-readable PDF ready for job applications."
>
	<section class="guide-grid">
		<article class="guide-card emphasis">
			<p class="guide-kicker">What this adds</p>
			<h3>Build and export a clean CV that passes ATS screening.</h3>
			<p>
				Import your existing CV from PDF or DOCX, review and edit the extracted text, then
				download a professionally formatted PDF that any applicant tracking system can parse.
			</p>
		</article>

		<article class="guide-card">
			<p class="guide-kicker">Current scope</p>
			<h3>Upload, extract, edit, and export.</h3>
			<p>
				The extracted text gives you a fast starting point. Edit it to your liking, and
				download the final version as a clean PDF ready for submission.
			</p>
		</article>
	</section>

	<section class="builder-grid">
		<article class="editor-card">
			<div class="card-head">
				<div>
					<p class="guide-kicker">Editor</p>
					<h2>CV Content</h2>
				</div>
				<div class="meta-row">
					<span>{lineCount} lines</span>
					<span>{wordCount} words</span>
					<span>{cvText.length} characters</span>
					{#if importedSourceName}
						<span>Imported: {importedSourceName}</span>
					{/if}
				</div>
			</div>

			<div class="control-grid">
				<div class="field-row">
					<div class="field">
						<label for="fullname">Full name</label>
						<input
							id="fullname"
							type="text"
							bind:value={fullName}
							placeholder="Jane Doe"
							autocomplete="name"
						/>
					</div>

					<div class="field">
						<label for="filename">Download filename</label>
						<input
							id="filename"
							type="text"
							bind:value={fileName}
							placeholder="my_cv"
							autocomplete="off"
						/>
					</div>
				</div>

				<div class="actions">
					<input
						bind:this={documentUploadInput}
						type="file"
						accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
						class="hidden-upload"
						on:change={handleDocumentImport}
					/>
					
					<button
						class="secondary-button"
						type="button"
						on:click={() => documentUploadInput?.click()}
						disabled={importingDocument}
					>
						{importingDocument ? 'Importing...' : 'Import PDF/DOCX'}
					</button>
					
					<button 
						class="secondary-button" 
						type="button" 
						on:click={copyText}
					>
						Copy text
					</button>
					
					<button 
						class="secondary-button" 
						type="button" 
						on:click={clearEditor}
					>
						Clear
					</button>
					
					<button
						class="primary-button"
						type="button"
						on:click={downloadPdf}
						disabled={generatingPdf || !cvText.trim()}
					>
						{generatingPdf ? 'Generating...' : 'Download PDF'}
					</button>
				</div>
			</div>

			{#if notice}
				<p class:error={noticeTone === 'error'} class="notice">{notice}</p>
			{/if}

			<textarea
				bind:value={cvText}
				class="cv-editor"
				spellcheck="true"
				placeholder="Paste or edit your CV text here..."
			></textarea>
		</article>

		<div class="side-column">
			<article class="side-card">
				<p class="guide-kicker">Imported source</p>
				<h3>Extracted text preview</h3>
				{#if extractedText}
					<p>
						Extracted from <strong>{importedSourceName}</strong>. This is the raw text
						used to populate the editor.
					</p>
					<pre class="source-preview">{extractedText.slice(0, 500)}{extractedText.length > 500 ? '...' : ''}</pre>
				{:else}
					<p>Import a PDF or DOCX and the extracted text will appear here for review.</p>
				{/if}
			</article>

			<article class="side-card">
				<p class="guide-kicker">Formatting Tips</p>
				<h3>Make your CV ATS-friendly</h3>
				<ul class="tips-list">
					<li>Use simple section headers like EXPERIENCE, EDUCATION, SKILLS</li>
					<li>Stick to standard fonts (the PDF uses Helvetica)</li>
					<li>Avoid tables, columns, and graphics</li>
					<li>Use bullet points with action verbs</li>
					<li>Include keywords from the job description</li>
					<li>Save as PDF for best compatibility</li>
				</ul>
			</article>

			<article class="side-card">
				<p class="guide-kicker">Quick Stats</p>
				<h3>Document overview</h3>
				<div class="stats-grid">
					<div class="stat-item">
						<span class="stat-number">{lineCount}</span>
						<span class="stat-label">Lines</span>
					</div>
					<div class="stat-item">
						<span class="stat-number">{wordCount}</span>
						<span class="stat-label">Words</span>
					</div>
					<div class="stat-item">
						<span class="stat-number">{cvText.length}</span>
						<span class="stat-label">Characters</span>
					</div>
				</div>
			</article>

			<article class="side-card">
				<p class="guide-kicker">Next Steps</p>
				<h3>After downloading</h3>
				<ul class="tips-list">
					<li>Use the Job Search page to find matching positions</li>
					<li>Tailor your CV for specific job descriptions</li>
					<li>Keep your CV updated with new skills and experience</li>
					<li>Download a fresh PDF for each application</li>
				</ul>
			</article>
		</div>
	</section>
</AppShell>

<style>
	.guide-grid,
	.builder-grid {
		display: grid;
		gap: 1.25rem;
	}

	.guide-grid {
		grid-template-columns: repeat(2, minmax(0, 1fr));
		margin-bottom: 1.25rem;
	}

	.builder-grid {
		grid-template-columns: minmax(0, 1.45fr) minmax(320px, 0.95fr);
		align-items: start;
	}

	.guide-card,
	.editor-card,
	.side-card {
		border: 1px solid rgba(122, 146, 171, 0.26);
		border-radius: 1.5rem;
		background: rgba(255, 255, 255, 0.9);
		box-shadow: 0 20px 40px rgba(25, 47, 74, 0.08);
	}

	.guide-card,
	.side-card {
		padding: 1.5rem;
	}

	.editor-card {
		padding: 1.5rem;
	}

	.emphasis {
		background:
			linear-gradient(135deg, rgba(24, 82, 161, 0.96), rgba(33, 125, 153, 0.9)),
			rgba(255, 255, 255, 0.9);
		color: #f4f8ff;
	}

	.emphasis .guide-kicker,
	.emphasis h3,
	.emphasis p {
		color: inherit;
	}

	.guide-kicker {
		margin: 0 0 0.6rem;
		text-transform: uppercase;
		letter-spacing: 0.14em;
		font-size: 0.74rem;
		font-weight: 700;
		color: #567493;
	}

	.guide-card h3,
	.card-head h2,
	.side-card h3 {
		margin: 0 0 0.65rem;
		color: #16324f;
	}

	.guide-card p,
	.side-card p,
	.card-head p,
	.notice,
	.field label {
		color: #4b6782;
	}

	.card-head,
	.control-grid {
		display: flex;
		align-items: flex-start;
		justify-content: space-between;
		gap: 1rem;
	}

	.control-grid {
		flex-direction: column;
		margin: 1.2rem 0 0.8rem;
	}

	.meta-row,
	.actions,
	.stats-grid {
		display: flex;
		flex-wrap: wrap;
		gap: 0.75rem;
	}

	.meta-row span {
		padding: 0.5rem 0.8rem;
		border-radius: 999px;
		font-size: 0.9rem;
		font-weight: 700;
		color: #30506f;
		background: rgba(232, 239, 248, 0.95);
	}

	.stats-grid {
		margin-top: 0.5rem;
	}

	.stat-item {
		display: flex;
		flex-direction: column;
		align-items: center;
		padding: 0.75rem;
		border-radius: 1rem;
		background: rgba(248, 251, 255, 0.98);
		min-width: 80px;
	}

	.stat-number {
		font-size: 1.5rem;
		font-weight: 700;
		color: #2563eb;
	}

	.stat-label {
		font-size: 0.75rem;
		color: #64748b;
		text-transform: uppercase;
		letter-spacing: 0.1em;
	}

	.field {
		display: grid;
		gap: 0.55rem;
		width: min(100%, 320px);
	}

	.field-row {
		display: flex;
		flex-wrap: wrap;
		gap: 1rem;
	}

	.field label {
		font-size: 0.95rem;
		font-weight: 700;
	}

	.field input,
	.cv-editor {
		width: 100%;
		border: 1px solid rgba(133, 154, 178, 0.38);
		border-radius: 1rem;
		background: rgba(248, 251, 255, 0.98);
		color: #16324f;
	}

	.field input {
		padding: 0.9rem 1rem;
		font: inherit;
	}

	.actions {
		align-items: center;
	}

	.primary-button,
	.secondary-button {
		border: none;
		border-radius: 999px;
		padding: 0.8rem 1.15rem;
		font-size: 0.95rem;
		font-weight: 700;
		cursor: pointer;
		transition:
			transform 0.2s ease,
			box-shadow 0.2s ease,
			background 0.2s ease;
	}

	.primary-button {
		color: #f8fbff;
		background: linear-gradient(135deg, #0f3769, #2563eb);
		box-shadow: 0 14px 24px rgba(37, 99, 235, 0.24);
	}

	.secondary-button {
		color: #21425f;
		background: rgba(237, 243, 249, 0.96);
	}

	.primary-button:hover,
	.secondary-button:hover {
		transform: translateY(-1px);
	}

	.primary-button:disabled,
	.secondary-button:disabled {
		cursor: not-allowed;
		opacity: 0.7;
		transform: none;
	}

	.hidden-upload {
		display: none;
	}

	.notice {
		margin: 0 0 0.9rem;
		font-weight: 600;
	}

	.notice.error {
		color: #b42318;
	}

	.cv-editor {
		min-height: 720px;
		padding: 1.2rem;
		resize: vertical;
		font-family: 'SFMono-Regular', 'Menlo', 'Consolas', monospace;
		font-size: 0.96rem;
		line-height: 1.65;
	}

	.source-preview {
		margin: 0;
		max-height: 280px;
		overflow: auto;
		padding: 1rem;
		border-radius: 1rem;
		border: 1px solid rgba(133, 154, 178, 0.28);
		background: rgba(246, 249, 252, 0.96);
		color: #21425f;
		font-family: 'SFMono-Regular', 'Menlo', 'Consolas', monospace;
		font-size: 0.9rem;
		line-height: 1.55;
		white-space: pre-wrap;
		word-break: break-word;
	}

	.side-column {
		display: grid;
		gap: 1.25rem;
	}

	.tips-list {
		margin: 0;
		padding-left: 1.1rem;
		color: #4b6782;
		line-height: 1.65;
	}

	@media (max-width: 960px) {
		.guide-grid,
		.builder-grid {
			grid-template-columns: 1fr;
		}

		.card-head,
		.control-grid {
			flex-direction: column;
		}

		.field {
			width: 100%;
		}

		.field-row {
			flex-direction: column;
		}

		.cv-editor {
			min-height: 560px;
		}
	}
</style>
