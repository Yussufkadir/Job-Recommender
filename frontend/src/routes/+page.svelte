<script lang="ts">
	import HeroSection from '$lib/components/HeroSection.svelte';
	import type { PageData } from './$types';

	export let data: PageData;
</script>

<div class="home-shell">
	<nav class="nav-overlay">
		<a class="cta-button login" href="/login">Login</a>
		<a class="cta-button signup" href="/signup">Sign Up</a>
	</nav>

	<HeroSection content={data.hero} />
</div>

<style>
	.home-shell {
		position: relative;
		min-height: 100vh;
	}

	.nav-overlay {
		position: fixed;
		top: 1.5rem;
		right: 2rem;
		display: flex;
		gap: 1rem;
		z-index: 100;
		.nav-overlay {
			position: fixed;
			top: 1.5rem;
			right: 2rem;
			display: flex;
			gap: 1rem;
			z-index: 100;
		}
	}

	.cta-button {
		padding: 0.6rem 1.4rem;
		border-radius: 999px;
		text-decoration: none;
		font-weight: 600;

		transition:
			transform 0.2s,
			box-shadow 0.2s;
		font-size: 0.95rem;
	}

	.cta-button:hover {
		transform: translateY(-2px);
		box-shadow: 0 10px 20px rgba(0, 0, 0, 0.2);
	}

	.login {
		background: #0e11ee;
		color: #f8fafc;
		border: 1px solid #112a60;
	}

	.signup {
		background: #0e11ee;
		color: white;
		border: 1px solid #112a60;
	}

	@media (max-width: 600px) {
		.nav-overlay {
			right: 1rem;
			top: 1rem;
			gap: 0.5rem;
		}
	}
</style>
