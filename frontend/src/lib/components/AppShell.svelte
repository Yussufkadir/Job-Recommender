<script lang="ts">
	import { browser } from '$app/environment';
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { onDestroy, onMount } from 'svelte';
	import { logout, userToken } from '$lib/auth';

	export let heading = '';
	export let subheading = '';
	export let eyebrow = 'Workspace';

	const navItems = [
		{ href: '/main_page', label: 'Overview' },
		{ href: '/job_search', label: 'Job Search' },
		{ href: '/cv_builder', label: 'CV Builder' },
		{ href: '/tracker', label: 'Tracker' }
	];

	let token: string | null = null;
	let ready = false;

	const unsubscribe = userToken.subscribe((value) => {
		token = value;

		if (ready && browser && !value) {
			goto('/login');
		}
	});

	function isActive(pathname: string, href: string) {
		return pathname === href || pathname.startsWith(`${href}/`);
	}

	onMount(() => {
		ready = true;

		if (!token) {
			goto('/login');
		}
	});

	onDestroy(unsubscribe);
</script>

{#if !ready}
	<div class="auth-loading">Preparing your workspace...</div>
{:else if token}
	<div class="app-shell">
		<div class="backdrop glow-left"></div>
		<div class="backdrop glow-right"></div>

		<header class="topbar">
			<div class="brand-block">
				<a class="brand-mark" href="/main_page" aria-label="Go to overview">JR</a>
				<div>
					<p class="brand-kicker">Career Workspace</p>
					<h1>Job Recommender</h1>
				</div>
			</div>

			<nav class="topnav" aria-label="Application sections">
				{#each navItems as item (item.href)}
					<a
						href={item.href}
						class:active={isActive($page.url.pathname, item.href)}
						class="nav-pill"
					>
						{item.label}
					</a>
				{/each}
			</nav>

			<button type="button" class="logout-button" on:click={logout}>Log out</button>
		</header>

		<main class="content">
			<section class="page-intro">
				<p class="eyebrow">{eyebrow}</p>
				<h2>{heading}</h2>
				{#if subheading}
					<p class="subheading">{subheading}</p>
				{/if}
			</section>

			<div class="page-content">
				<slot />
			</div>
		</main>
	</div>
{/if}

<style>
	:global(body) {
		font-family: 'Avenir Next', 'Segoe UI', 'Helvetica Neue', sans-serif;
	}

	.auth-loading {
		min-height: 100vh;
		display: grid;
		place-items: center;
		font-size: 1rem;
		font-weight: 600;
		color: #23405d;
	}

	.app-shell {
		position: relative;
		min-height: 100vh;
		padding: 1.5rem;
		background:
			radial-gradient(circle at top left, rgba(244, 245, 246, 0.995), transparent 30%),
			radial-gradient(circle at top right, rgba(246, 247, 250, 0.95), transparent 26%),
			linear-gradient(180deg, #f4f8fc 0%, #eef3f8 100%);
	}

	.backdrop {
		position: fixed;
		border-radius: 999px;
		filter: blur(80px);
		pointer-events: none;
		opacity: 0.6;
	}

	.glow-left {
		top: 6rem;
		left: -4rem;
		width: 16rem;
		height: 16rem;
		background: rgba(238, 239, 242, 0.935);
	}

	.glow-right {
		top: 12rem;
		right: 0;
		width: 18rem;
		height: 18rem;
		background: rgba(255, 255, 255, 0.989);
	}

	.topbar {
		position: sticky;
		top: 1rem;
		z-index: 20;
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 1rem;
		max-width: 1280px;
		margin: 0 auto 1.5rem;
		padding: 1rem 1.2rem;
		border: 1px solid rgba(138, 160, 185, 0.35);
		border-radius: 1.5rem;
		background: rgba(255, 255, 255, 0.854);
		backdrop-filter: blur(20px);
	}

	.brand-block {
		display: flex;
		align-items: center;
		gap: 0.9rem;
		min-width: 0;
	}

	.brand-mark {
		display: grid;
		place-items: center;
		width: 3rem;
		height: 3rem;
		border-radius: 1rem;
		text-decoration: none;
		font-weight: 800;
		letter-spacing: 0.08em;
		color: #f8fbff;
		background: linear-gradient(135deg, #143b6b, #0e11ee);
		box-shadow: 0 16px 24px rgba(37, 99, 235, 0.24);
	}

	.brand-kicker,
	.eyebrow {
		margin: 0;
		text-transform: uppercase;
		letter-spacing: 0.14em;
		font-size: 0.74rem;
		font-weight: 700;
		color: #527194;
	}

	.brand-block h1,
	.page-intro h2 {
		margin: 0;
		color: #16324f;
	}

	.brand-block h1 {
		font-size: 1rem;
	}

	.topnav {
		display: flex;
		align-items: center;
		gap: 0.6rem;
		flex-wrap: wrap;
		justify-content: center;
	}

	.nav-pill {
		padding: 0.75rem 1rem;
		border-radius: 999px;
		text-decoration: none;
		font-weight: 700;
		color: #0e11ee;
		background: transparent;
		border: 1px solid transparent;
		transition:
			background 0.2s ease,
			color 0.2s ease,
			transform 0.2s ease,
			border-color 0.2s ease;
	}

	.nav-pill:hover,
	.nav-pill.active {
		transform: translateY(-1px);
		color: #173557;
		border-color: rgba(88, 120, 160, 0.26);
		background: rgba(255, 255, 255, 0.92);
	}

	.logout-button {
		border: none;
		border-radius: 999px;
		padding: 0.8rem 1.25rem;
		font-weight: 700;
		cursor: pointer;
		color: #f8fbff;
		background: linear-gradient(135deg, #0e11ee);
		box-shadow: 0 14px 24px rgba(17, 46, 84, 0.18);
	}

	.content {
		position: relative;
		z-index: 1;
		max-width: 1280px;
		margin: 0 auto;
	}

	.page-intro {
		display: flex;
		flex-direction: column;
		gap: 0.65rem;
		margin-bottom: 1.5rem;
		padding: 0.75rem 0.25rem 0;
	}

	.page-intro h2 {
		font-size: clamp(2rem, 3vw, 3.2rem);
		line-height: 1.02;
		max-width: 12ch;
	}

	.subheading {
		max-width: 52rem;
		margin: 0;
		font-size: 1rem;
		line-height: 1.65;
		color: #4b6580;
	}

	.page-content {
		padding-bottom: 2rem;
	}

	@media (max-width: 960px) {
		.topbar {
			position: static;
			flex-direction: column;
			align-items: stretch;
		}

		.brand-block {
			justify-content: flex-start;
		}

		.topnav {
			justify-content: flex-start;
		}

		.logout-button {
			width: 100%;
		}
	}

	@media (max-width: 640px) {
		.app-shell {
			padding: 1rem;
		}

		.topbar {
			padding: 1rem;
			border-radius: 1.2rem;
		}

		.nav-pill {
			flex: 1 1 calc(50% - 0.4rem);
			text-align: center;
		}
	}
</style>
