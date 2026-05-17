<script lang="ts">
	import { onMount } from 'svelte';
	import AppShell from '$lib/components/AppShell.svelte';
	import { getApplications, updateApplicationStatus } from '$lib/api/applications';
	import type { Application, ApplicationStatus } from '$lib/types/application';

	const statuses: ApplicationStatus[] = ['saved', 'applied', 'interview', 'offer', 'rejected'];
	const statusLabels: Record<ApplicationStatus, string> = {
		saved: 'Saved',
		applied: 'Applied',
		interview: 'Interview',
		offer: 'Offer',
		rejected: 'Rejected'
	};

	let applications: Application[] = [];
	let loading = true;
	let error = '';
	let filter: ApplicationStatus | 'all' = 'all';

	$: filtered =
		filter === 'all'
			? applications
			: applications.filter((application) => application.status === filter);

	async function loadData() {
		loading = true;
		error = '';

		try {
			applications = await getApplications();
		} catch (err) {
			console.error(err);
			error = 'Could not load applications.';
		} finally {
			loading = false;
		}
	}

	async function onStatusChange(app: Application, next: string) {
		const nextStatus = next as ApplicationStatus;
		const previousStatus = app.status;

		app.status = nextStatus;

		try {
			const updated = await updateApplicationStatus(app.id, nextStatus);
			app.status = updated.status;
			app.updated_at = updated.updated_at;
		} catch (err) {
			console.error(err);
			app.status = previousStatus;
			error = 'Status update failed.';
		}
	}

	function formatDateTime(value: string) {
		return new Intl.DateTimeFormat('en', {
			month: 'short',
			day: 'numeric',
			year: 'numeric',
			hour: 'numeric',
			minute: '2-digit'
		}).format(new Date(value));
	}

	onMount(loadData);

	$: statusCounts = statuses.map((status) => ({
		status,
		label: statusLabels[status],
		count: applications.filter((app) => app.status === status).length
	}));
</script>

<svelte:head>
	<title>Tracker | Job Recommender</title>
</svelte:head>

<AppShell
	eyebrow="Pipeline Tracker"
	heading="Keep every application moving through a clear pipeline."
	subheading="This tab is built for maintenance: filtering, refreshing, and updating status without losing sight of what needs follow-up."
>
	<section class="tracker-summary">
		<div class="filter-card">
			<div>
				<p class="section-kicker">Controls</p>
				<h3>Filter your pipeline</h3>
			</div>
			<div class="control-row">
				<label for="filter">Stage</label>
				<select id="filter" bind:value={filter}>
					<option value="all">All statuses</option>
					{#each statuses as status (status)}
						<option value={status}>{statusLabels[status]}</option>
					{/each}
				</select>
				<button type="button" on:click={loadData}>Refresh</button>
			</div>
		</div>

		<div class="summary-grid">
			{#each statusCounts as item (item.status)}
				<div class={`summary-tile ${item.status}`}>
					<span>{item.label}</span>
					<strong>{item.count}</strong>
				</div>
			{/each}
		</div>
	</section>

	{#if loading}
		<section class="state-panel">
			<h3>Loading your applications...</h3>
		</section>
	{:else if error}
		<section class="state-panel error">
			<h3>{error}</h3>
		</section>
	{:else if filtered.length === 0}
		<section class="state-panel">
			<h3>No applications match this filter yet.</h3>
			<p>Try a different stage or add more roles through the job search workspace.</p>
			<a href="/job_search">Go to job search</a>
		</section>
	{:else}
		<section class="application-list">
			{#each filtered as app (app.id)}
				<article class="application-card">
					<div class="card-head">
						<div>
							<h3>{app.job_title}</h3>
							<p>{app.company}</p>
						</div>
						<span class={`status-pill ${app.status}`}>{statusLabels[app.status]}</span>
					</div>

					<div class="card-body">
						<div class="meta-group">
							<span>Updated {formatDateTime(app.updated_at)}</span>
							{#if app.job_url}
								<a href={app.job_url} target="_blank" rel="noreferrer">Open job link</a>
							{/if}
						</div>

						<label class="status-editor">
							<span>Move to</span>
							<select
								value={app.status}
								on:change={(event) =>
									onStatusChange(app, (event.currentTarget as HTMLSelectElement).value)}
							>
								{#each statuses as status (status)}
									<option value={status}>{statusLabels[status]}</option>
								{/each}
							</select>
						</label>

						{#if app.notes}
							<p class="notes">{app.notes}</p>
						{/if}
					</div>
				</article>
			{/each}
		</section>
	{/if}
</AppShell>

<style>
	.tracker-summary,
	.summary-grid,
	.application-list {
		display: grid;
		gap: 1rem;
	}

	.filter-card,
	.application-card,
	.summary-tile,
	.state-panel {
		border: 1px solid rgba(138, 160, 185, 0.26);
		border-radius: 1.5rem;
		background: rgba(250, 252, 255, 0.9);
		box-shadow: 0 22px 42px rgba(31, 51, 84, 0.08);
	}

	.filter-card {
		display: flex;
		justify-content: space-between;
		align-items: flex-end;
		gap: 1rem;
		padding: 1.3rem;
	}

	.section-kicker {
		margin: 0 0 0.45rem;
		text-transform: uppercase;
		letter-spacing: 0.12em;
		font-size: 0.76rem;
		font-weight: 700;
		color: #5d7898;
	}

	.filter-card h3,
	.application-card h3,
	.state-panel h3 {
		margin: 0;
		color: #16324f;
	}

	.control-row {
		display: flex;
		flex-wrap: wrap;
		align-items: center;
		gap: 0.75rem;
	}

	.control-row label,
	.status-editor span {
		font-weight: 700;
		color: #24405d;
	}

	.control-row select,
	.status-editor select {
		min-width: 170px;
		padding: 0.8rem 1rem;
		border-radius: 1rem;
		border: 1px solid #d6e1ec;
		background: rgba(255, 255, 255, 0.92);
		color: #173557;
	}

	.control-row button,
	.state-panel a {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		padding: 0.85rem 1.15rem;
		border-radius: 999px;
		border: none;
		text-decoration: none;
		font-weight: 700;
		color: #f8fbff;
		background: linear-gradient(135deg, #143b6b, #2563eb);
		cursor: pointer;
	}

	.summary-grid {
		grid-template-columns: repeat(5, minmax(0, 1fr));
	}

	.summary-tile {
		padding: 1rem;
	}

	.summary-tile span,
	.application-card p,
	.meta-group span,
	.notes,
	.state-panel p {
		color: #5b7188;
	}

	.summary-tile span {
		display: block;
		font-size: 0.8rem;
		font-weight: 700;
		text-transform: uppercase;
		letter-spacing: 0.08em;
		margin-bottom: 0.45rem;
	}

	.summary-tile strong {
		font-size: 1.8rem;
		color: #173557;
	}

	.summary-tile.saved {
		background: linear-gradient(135deg, rgba(228, 238, 248, 0.95), rgba(250, 252, 255, 0.95));
	}

	.summary-tile.applied {
		background: linear-gradient(135deg, rgba(232, 244, 231, 0.95), rgba(250, 252, 255, 0.95));
	}

	.summary-tile.interview {
		background: linear-gradient(135deg, rgba(255, 242, 217, 0.95), rgba(250, 252, 255, 0.95));
	}

	.summary-tile.offer {
		background: linear-gradient(135deg, rgba(229, 248, 240, 0.95), rgba(250, 252, 255, 0.95));
	}

	.summary-tile.rejected {
		background: linear-gradient(135deg, rgba(252, 231, 231, 0.95), rgba(250, 252, 255, 0.95));
	}

	.application-list {
		margin-top: 1rem;
	}

	.application-card {
		padding: 1.25rem;
	}

	.card-head,
	.meta-group {
		display: flex;
		justify-content: space-between;
		gap: 1rem;
	}

	.card-head {
		align-items: flex-start;
		margin-bottom: 1rem;
	}

	.card-head p {
		margin: 0.35rem 0 0;
	}

	.status-pill {
		padding: 0.45rem 0.85rem;
		border-radius: 999px;
		font-size: 0.82rem;
		font-weight: 700;
		text-transform: capitalize;
		white-space: nowrap;
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

	.card-body {
		display: grid;
		gap: 0.95rem;
	}

	.meta-group {
		align-items: center;
		flex-wrap: wrap;
	}

	.meta-group a {
		color: #22528d;
		font-weight: 700;
		text-decoration: none;
	}

	.status-editor {
		display: grid;
		gap: 0.45rem;
		max-width: 260px;
	}

	.notes {
		margin: 0;
		line-height: 1.6;
	}

	.state-panel {
		display: grid;
		justify-items: flex-start;
		gap: 0.75rem;
		padding: 1.4rem;
		margin-top: 1rem;
	}

	.state-panel p {
		margin: 0;
	}

	.state-panel.error h3 {
		color: #b42318;
	}

	@media (max-width: 960px) {
		.summary-grid {
			grid-template-columns: repeat(2, minmax(0, 1fr));
		}

		.filter-card {
			flex-direction: column;
			align-items: stretch;
		}

		.control-row {
			align-items: stretch;
		}
	}

	@media (max-width: 640px) {
		.summary-grid {
			grid-template-columns: 1fr;
		}

		.card-head,
		.meta-group {
			flex-direction: column;
			align-items: flex-start;
		}

		.status-editor {
			max-width: none;
		}
	}
</style>
