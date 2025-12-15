<script lang="ts">
	import favicon from '$lib/assets/favicon.svg';

	let { children } = $props();
</script>

<svelte:head>
	<link rel="icon" href={favicon} />
</svelte:head>

<div class="layout-frame">
	{@render children()}
</div>

<style>
	:global(html) {
		height: 100%;
		background: #0f172a;
	}

	:global(body) {
		font-family:
			system-ui,
			-apple-system,
			BlinkMacSystemFont,
			'Segoe UI',
			Roboto,
			Oxygen,
			Ubuntu,
			Cantarell,
			'Open Sans',
			'Helvetica Neue',
			sans-serif;
		margin: 0;
		color: #f8fafc;
		min-height: 100vh;
		background: radial-gradient(circle at top, #1e293b 0%, #020617 100%);
		background-attachment: fixed;
		background-size: cover;
		background-repeat: no-repeat;
		scrollbar-gutter: stable;
		overflow-y: scroll;
		overflow-x: hidden;
	}

	.layout-frame {
		position: relative;
		min-height: 100vh;
	}
</style>
