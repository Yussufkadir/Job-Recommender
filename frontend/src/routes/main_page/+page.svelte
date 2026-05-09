<script lang="ts">
	import { onMount } from 'svelte';
	import AppShell from '$lib/components/AppShell.svelte';
	import { getApplications } from '$lib/api/applications';
	import type { Application, ApplicationStatus } from '$lib/types/application';

	type StatusSummary = {
		status: ApplicationStatus;
		label: string;
		description: string;
	};

	const statusSummaries: StatusSummary[] = [
		{ status: 'saved', label: 'Saved', description: 'Interesting roles you may come back to.' },
		{ status: 'applied', label: 'Applied', description: 'Applications already sent out.' },
		{ status: 'interview', label: 'Interview', description: 'Conversations in progress.' },
		{ status: 'offer', label: 'Offer', description: 'Opportunities close to the finish line.' },
		{ status: 'rejected', label: 'Rejected', description: 'Closed loops you can learn from.' }
	];

	let applications: Application[] = [];
	let loading = true;
	let error = '';

	async function loadDashboard() {
		loading = true;
		error = '';

		try {
			applications = await getApplications();
		} catch (err) {
			console.error(err);
			error = 'Could not load your application summary just now.';
		} finally {
			loading = false;
		}
	}

	function formatDate(value: string) {
		return new Intl.DateTimeFormat('en', {
			month: 'short',
			day: 'numeric',
			year: 'numeric'
		}).format(new Date(value));
	}

	onMount(loadDashboard);

	$: totalApplications = applications.length;
	$: activePipeline = applications.filter((app) =>
		['saved', 'applied', 'interview', 'offer'].includes(app.status)
	).length;
	$: positiveMomentum = applications.filter((app) =>
		['interview', 'offer'].includes(app.status)
	).length;
	$: conversionRate = totalApplications
		? Math.round(
				(applications.filter((app) => app.status !== 'saved').length / totalApplications) * 100
			)
		: 0;
	$: latestActivity = applications[0]?.updated_at ?? null;
	$: recentApplications = applications.slice(0, 5);
	$: statusCards = statusSummaries.map((summary) => {
		const count = applications.filter((app) => app.status === summary.status).length;

		return {
			...summary,
			count,
			share: totalApplications ? Math.round((count / totalApplications) * 100) : 0
		};
	});
</script>

<svelte:head>
	<title>Overview | Job Recommender</title>
</svelte:head>

<AppShell
	eyebrow="Main Hub"
	heading="See the full picture before you dive into the next task."
	subheading="This overview gives you one place for pipeline stats, recent activity, and shortcuts into the parts of the product that do the real work."
>
	<section class="hero-grid">
		<article class="hero-card spotlight">
			<div class="hero-copy">
				<p class="kicker">Today&apos;s focus</p>
				<h3>Run the app like a workspace, not a single page.</h3>
				<p>
					Start from a summary here, jump into job search when you want fresh leads, and keep
					tracker updates flowing in one connected rhythm.
				</p>
			</div>

			<div class="hero-actions">
				<a href="/job_search" class="primary-action">Open job search</a>
				<a href="/tracker" class="secondary-action">Review tracker</a>
			</div>
		</article>

		<article class="hero-card stats">
			<div class="stat-tile">
				<span>Total tracked</span>
				<strong>{loading ? '...' : totalApplications}</strong>
				<small>Applications currently in your workspace.</small>
			</div>
			<div class="stat-tile">
				<span>Active pipeline</span>
				<strong>{loading ? '...' : activePipeline}</strong>
				<small>Saved, applied, interview, and offer stages combined.</small>
			</div>
			<div class="stat-tile">
				<span>Interview momentum</span>
				<strong>{loading ? '...' : positiveMomentum}</strong>
				<small>Roles already moving into interviews or offers.</small>
			</div>
			<div class="stat-tile">
				<span>Action rate</span>
				<strong>{loading ? '...' : `${conversionRate}%`}</strong>
				<small>Tracked roles that moved beyond the saved stage.</small>
			</div>
		</article>
	</section>

	<section class="dashboard-grid">
		<article class="panel">
			<div class="section-head">
				<div>
					<p class="section-kicker">Status snapshot</p>
					<h3>Pipeline breakdown</h3>
				</div>
				{#if latestActivity}
					<span class="section-note">Last activity: {formatDate(latestActivity)}</span>
				{/if}
			</div>

			{#if loading}
				<p class="state-copy">Loading your application stats...</p>
			{:else if error}
				<p class="state-copy error">{error}</p>
			{:else if totalApplications === 0}
				<div class="empty-panel">
					<h4>No application history yet</h4>
					<p>
						Once you start tracking roles, this page will turn into your command center for
						progress, follow-ups, and momentum.
					</p>
					<a href="/job_search" class="secondary-action">Search your first role</a>
				</div>
			{:else}
				<div class="status-grid">
					{#each statusCards as card}
						<div class="status-card">
							<div class="status-card-head">
								<div>
									<h4>{card.label}</h4>
									<p>{card.description}</p>
								</div>
								<strong>{card.count}</strong>
							</div>
							<div class="progress-track">
								<div class="progress-bar" style={`width: ${card.share}%`}></div>
							</div>
							<span class="progress-label">{card.share}% of your tracked roles</span>
						</div>
					{/each}
				</div>
			{/if}
		</article>

		<article class="panel">
			<div class="section-head">
				<div>
					<p class="section-kicker">Quick actions</p>
					<h3>Pick your next move</h3>
				</div>
			</div>

			<div class="action-stack">
				<a class="action-card" href="/job_search">
					<span class="action-index">01</span>
					<div>
						<h4>Search and tailor jobs</h4>
						<p>Upload a CV, refine the target role, and generate better-fit recommendations.</p>
					</div>
				</a>

				<a class="action-card" href="/tracker">
					<span class="action-index">02</span>
					<div>
						<h4>Keep applications current</h4>
						<p>Update role status, refresh priorities, and keep the pipeline from getting stale.</p>
					</div>
				</a>

				<a class="action-card" href="/cv_builder">
					<span class="action-index">03</span>
					<div>
						<h4>Build a LaTeX CV</h4>
						<p>Draft, edit, and download your resume source in a dedicated builder workspace.</p>
					</div>
				</a>
			</div>
		</article>

		<article class="panel full-width">
			<div class="section-head">
				<div>
					<p class="section-kicker">Recent activity</p>
					<h3>Most recently updated applications</h3>
				</div>
			</div>

			{#if loading}
				<p class="state-copy">Pulling in the latest activity...</p>
			{:else if error}
				<p class="state-copy error">{error}</p>
			{:else if recentApplications.length === 0}
				<p class="state-copy">
					No recent activity yet. As soon as you save or update roles, they will appear here.
				</p>
			{:else}
				<div class="recent-list">
					{#each recentApplications as application}
						<div class="recent-row">
							<div>
								<h4>{application.job_title}</h4>
								<p>{application.company}</p>
							</div>
							<div class="recent-meta">
								<span class={`status-pill ${application.status}`}>{application.status}</span>
								<span>{formatDate(application.updated_at)}</span>
							</div>
						</div>
					{/each}
				</div>
			{/if}
		</article>
	</section>
</AppShell>

<style>
	.hero-grid,
	.dashboard-grid {
		display: grid;
		gap: 1.25rem;
	}

	.hero-grid {
		grid-template-columns: minmax(0, 1.35fr) minmax(0, 1fr);
		margin-bottom: 1.25rem;
	}

	.dashboard-grid {
		grid-template-columns: repeat(2, minmax(0, 1fr));
	}

	.hero-card,
	.panel {
		border: 1px solid rgba(136, 158, 182, 0.25);
		border-radius: 1.8rem;
		background: rgba(250, 252, 255, 0.88);
		box-shadow: 0 24px 45px rgba(31, 51, 84, 0.08);
		backdrop-filter: blur(18px);
	}

	.hero-card {
		padding: 1.6rem;
	}

	.spotlight {
		display: flex;
		flex-direction: column;
		justify-content: space-between;
		gap: 2rem;
		background: linear-gradient(135deg, rgba(18, 52, 96, 0.98), rgba(34, 82, 153, 0.95)), #143b6b;
		color: #f7fbff;
	}

	.kicker,
	.section-kicker {
		margin: 0 0 0.45rem;
		text-transform: uppercase;
		letter-spacing: 0.12em;
		font-size: 0.76rem;
		font-weight: 700;
		color: #7b98bb;
	}

	.spotlight .kicker {
		color: rgba(205, 224, 255, 0.86);
	}

	.hero-copy h3,
	.section-head h3,
	.status-card h4,
	.action-card h4,
	.empty-panel h4,
	.recent-row h4 {
		margin: 0;
		color: inherit;
	}

	.hero-copy h3 {
		font-size: clamp(1.7rem, 3vw, 2.6rem);
		line-height: 1.08;
		max-width: 11ch;
		margin-bottom: 0.9rem;
	}

	.hero-copy p {
		margin: 0;
		max-width: 34rem;
		line-height: 1.7;
		color: inherit;
	}

	.hero-actions {
		display: flex;
		flex-wrap: wrap;
		gap: 0.85rem;
	}

	.primary-action,
	.secondary-action {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		padding: 0.85rem 1.25rem;
		border-radius: 999px;
		font-weight: 700;
		text-decoration: none;
		transition:
			transform 0.2s ease,
			box-shadow 0.2s ease;
	}

	.primary-action:hover,
	.secondary-action:hover {
		transform: translateY(-1px);
	}

	.primary-action {
		color: #143b6b;
		background: #f8fbff;
		box-shadow: 0 16px 26px rgba(8, 20, 43, 0.22);
	}

	.secondary-action {
		color: #224c85;
		background: rgba(255, 255, 255, 0.78);
		border: 1px solid rgba(117, 146, 181, 0.25);
	}

	.stats {
		display: grid;
		grid-template-columns: repeat(2, minmax(0, 1fr));
		gap: 1rem;
	}

	.stat-tile {
		padding: 1.1rem;
		border-radius: 1.3rem;
		background: rgba(244, 248, 252, 0.88);
		border: 1px solid rgba(204, 218, 232, 0.7);
	}

	.stat-tile span,
	.progress-label,
	.section-note,
	.recent-row p,
	.action-card p,
	.status-card p,
	.empty-panel p,
	.state-copy,
	.stat-tile small {
		color: #5b7188;
	}

	.stat-tile span {
		display: block;
		font-size: 0.82rem;
		font-weight: 700;
		text-transform: uppercase;
		letter-spacing: 0.08em;
		margin-bottom: 0.6rem;
	}

	.stat-tile strong {
		display: block;
		margin-bottom: 0.35rem;
		font-size: 2rem;
		line-height: 1;
		color: #173557;
	}

	.panel {
		padding: 1.4rem;
	}

	.full-width {
		grid-column: 1 / -1;
	}

	.section-head {
		display: flex;
		justify-content: space-between;
		align-items: flex-start;
		gap: 1rem;
		margin-bottom: 1rem;
	}

	.status-grid,
	.action-stack,
	.recent-list {
		display: grid;
		gap: 0.95rem;
	}

	.status-card,
	.action-card,
	.recent-row,
	.empty-panel {
		border-radius: 1.35rem;
		padding: 1rem 1.05rem;
		background: rgba(255, 255, 255, 0.85);
		border: 1px solid rgba(208, 219, 231, 0.75);
	}

	.status-card-head,
	.recent-row,
	.recent-meta {
		display: flex;
		justify-content: space-between;
		gap: 1rem;
	}

	.status-card-head strong {
		font-size: 1.7rem;
		color: #173557;
	}

	.progress-track {
		margin-top: 0.9rem;
		height: 0.55rem;
		border-radius: 999px;
		background: #dfe8f1;
		overflow: hidden;
	}

	.progress-bar {
		height: 100%;
		border-radius: inherit;
		background: linear-gradient(90deg, #2563eb, #16a34a);
	}

	.action-card {
		display: grid;
		grid-template-columns: auto 1fr;
		gap: 1rem;
		text-decoration: none;
		color: #173557;
	}

	.action-card.muted {
		background: linear-gradient(135deg, rgba(232, 239, 247, 0.9), rgba(244, 248, 252, 0.9));
	}

	.action-index {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		width: 2.6rem;
		height: 2.6rem;
		border-radius: 0.95rem;
		background: #143b6b;
		color: #f7fbff;
		font-weight: 800;
	}

	.empty-panel {
		display: grid;
		gap: 0.8rem;
	}

	.recent-row h4 {
		margin-bottom: 0.25rem;
	}

	.recent-row p {
		margin: 0;
	}

	.recent-meta {
		align-items: center;
		flex-wrap: wrap;
		justify-content: flex-end;
		font-size: 0.92rem;
	}

	.status-pill {
		padding: 0.45rem 0.8rem;
		border-radius: 999px;
		font-size: 0.8rem;
		font-weight: 700;
		text-transform: capitalize;
	}

	.status-pill.saved {
		background: #e4eef8;
		color: #234d82;
	}

	.status-pill.applied {
		background: #e8f4e7;
		color: #22603b;
	}

	.status-pill.interview {
		background: #fff2d9;
		color: #8b5a14;
	}

	.status-pill.offer {
		background: #e5f8f0;
		color: #0f6a53;
	}

	.status-pill.rejected {
		background: #fce7e7;
		color: #9b2c2c;
	}

	.error {
		color: #b42318;
	}

	@media (max-width: 980px) {
		.hero-grid,
		.dashboard-grid {
			grid-template-columns: 1fr;
		}

		.full-width {
			grid-column: auto;
		}

		.hero-copy h3 {
			max-width: none;
		}
	}

	@media (max-width: 640px) {
		.hero-card,
		.panel {
			padding: 1.1rem;
			border-radius: 1.35rem;
		}

		.stats {
			grid-template-columns: 1fr;
		}

		.section-head,
		.status-card-head,
		.recent-row,
		.recent-meta {
			flex-direction: column;
			align-items: flex-start;
		}

		.hero-actions {
			flex-direction: column;
		}

		.primary-action,
		.secondary-action {
			width: 100%;
		}
	}
</style>
