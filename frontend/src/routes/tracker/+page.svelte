<script lang="ts">
	import { onMount } from 'svelte';
	import { getApplications, updateApplicationStatus } from '$lib/api/applications';
	import type { Application, ApplicationStatus } from '$lib/types/application';

	const statuses: ApplicationStatus[] = ['saved', 'applied', 'interview', 'offer', 'rejected'];

	let applications: Application[] = [];
	let loading = true;
	let error = '';
	let filter: ApplicationStatus | 'all' = 'all';

	$: filtered = filter == 'all' ? applications : applications.filter((a) => a.status === filter);

	async function loadData() {
		loading = true;
		error = '';
		try {
			applications = await getApplications();
		} catch (e) {
			error = 'Could not load applications.';
		} finally {
			loading = false;
		}
	}

	async function onStatusChange(app: Application, next: string) {
		const nextStatus = next as ApplicationStatus;
		const prev = app.status;
		app.status = nextStatus;

		try {
			const updated = await updateApplicationStatus(app.id, nextStatus);
			app.status = updated.status;
			app.updated_at = updated.updated_at;
		} catch {
			app.status = prev;
			error = 'Status update failed.';
		}
	}

	onMount(loadData);
</script>

<svelte:head>Application Tracking Page</svelte:head>

<div>
	<label for="filter">Filter:</label>
	<select id="filter" bind:value={filter}>
		<option value="all">all</option>
		{#each statuses as s}
			<option value={s}>{s}</option>
		{/each}
	</select>
	<button on:click={loadData}>Refresh</button>
</div>

{#if loading}
	<p>Loading...</p>
{:else if error}
	<p>{error}</p>
{:else if filtered.length === 0}
	<p>No applications found.</p>
{:else}
	<table>
		<thead>
			<tr>
				<th>Role</th>
				<th>Company</th>
				<th>Status</th>
				<th>Updated</th>
			</tr>
		</thead>
		<tbody>
			{#each filtered as app}
				<tr>
					<td>{app.job_title}</td>
					<td>{app.company}</td>
					<td>
						<select
							value={app.status}
							on:change={(e) => onStatusChange(app, (e.currentTarget as HTMLSelectElement).value)}
						>
							{#each statuses as s}
								<option value={s}>{s}</option>
							{/each}
						</select>
					</td>
					<td>{new Date(app.updated_at).toLocaleString()}</td>
				</tr>
			{/each}
		</tbody>
	</table>
{/if}
