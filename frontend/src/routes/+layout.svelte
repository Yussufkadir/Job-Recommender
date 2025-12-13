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
    :global(body){
        font-family: "Inter", "sans-serif";
        margin: 0;
        background: #0f172a;
        color: #f8fafc;
    }

	.layout-frame {
		position: relative;
		min-height: 100vh;
	}
</style>
