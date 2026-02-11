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
		background: #ffffff;
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
		color: #1e293b;
		min-height: 100vh;
		background: radial-gradient(circle at top, #ffffff 0%, #f8fafc 100%);
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
