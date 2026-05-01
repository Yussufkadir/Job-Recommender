<script lang="ts">
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import { setToken } from '$lib/auth';

	onMount(() => {
		const urlParams = new URLSearchParams(window.location.search);
		const token = urlParams.get('token');

		if (token) {
			setToken(token);
			goto('/main_page');
		} else {
			goto('/login?error=auth_failed');
		}
	});
</script>

<div
	style="display:flex; justify-content:center; align-items:center; height:100vh; background:#0f172a; color:white;"
>
	<h2>Logging you in...</h2>
</div>
