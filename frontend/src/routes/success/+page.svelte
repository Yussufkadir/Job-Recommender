<script lang="ts">
    import { onMount } from 'svelte';

    onMount(() => {
        const urlParams = new URLSearchParams(window.location.search);
        const token = urlParams.get('token');

        if (token) {
            localStorage.setItem('token', token);

            window.location.href = "/main_page";
        } else {
            window.location.href = "login?error=auth_failed";
        }
    });
</script>

<div style= "display=flex; justify-content: center; align-items: center; height: 100vh; background: #0f172a; color: white;">
    <h2>Logging you in...</h2>
</div>