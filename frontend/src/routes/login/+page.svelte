<script lang="ts">
	import { goto } from '$app/navigation';
	import { API_BASE } from '$lib/api';
	import { setToken } from '$lib/auth';

	let showPassword = false;
	let email = '';
	let password = '';
	let errorMessage = '';

	async function handleLogin() {
		errorMessage = '';

		try {
			const response = await fetch(`${API_BASE}/auth/login`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ email, password })
			});

			const data = await response.json();

			if (response.ok) {
				setToken(data.access_token);
				goto('/main_page');
			} else {
				errorMessage = data.detail || 'Login Failed';
			}
		} catch (error) {
			console.error('Login request failed.', error);
			errorMessage = 'Could not connect to the server.';
		}
	}
</script>

<svelte:head>
	<title>Sign In | Job Recommender</title>
</svelte:head>

<section class="page-shell">
<a href="/" class="back-link">Back to home</a>
	<section class="login-card">
		<header>
			<h2>Sign in to your account</h2>
			{#if errorMessage}
				<p class="error-text">{errorMessage}</p>
			{/if}
		</header>

		<form class="input-grid" on:submit|preventDefault={handleLogin}>
			<label>
				<span class="label-text">Email</span>
				<div class="input-wrap">
					<input class="text-input" type="email" placeholder="Email" bind:value={email} required />
				</div>
			</label>
			<label>
				<span class="label-text">Password</span>
				<div class="input-wrap">
					<input
						class="text-input"
						type={showPassword ? 'text' : 'password'}
						placeholder="*******"
						bind:value={password}
						required
					/>
					<button
						type="button"
						class="toggle-visibility"
						on:click={() => (showPassword = !showPassword)}
					>
						{showPassword ? 'Hide' : 'Show'}
					</button>
				</div>
			</label>
			<div class="actions">
				<button type="submit" class="primary-action">Log in</button>
			</div>
			<div style="text-align: center; margin-top: 0.5rem;">
				<a
					href="/forgot-password"
					style="color: #6366f1; font-size: 0.9rem; text-decoration: none;"
				>
					Forgot Password?
				</a>
			</div>
		</form>
		<div style="text-align: center;">
			<a href="/signup" style="color: #2563eb; font-size: 0.95rem; text-decoration: none;">
				Need an account? Sign up
			</a>
		</div>
	</section>
</section>

<style>
	.page-shell {
		min-height: 100vh;
		display: flex;
		align-items: center;
		justify-content: center;
		padding: 2rem;
		background: radial-gradient(circle at top, rgba(240, 240, 243, 0.823), transparent 60%);
	}

	.back-link {
		position: absolute;
		top: 2rem;
		left: 2rem;
		color: rgba(12, 15, 206, 0.761);
		text-decoration: none;
		font-weight: 600;
		font-size: 0.95rem;
		z-index: 10;
		transition: opacity 0.2s;
	}
	.back-link:hover {
		opacity: 0.8;
	}

	.login-card {
		max-width: 640px;
		margin: 2rem auto;
		padding: 1.75rem;
		border-radius: 1.5rem;
		background: rgba(254, 254, 255, 0.85);
		border: 1px solid rgba(32, 35, 209, 0.761);
		color: #0b0b0b;
		display: flex;
		flex-direction: column;
		gap: 1.25rem;
	}

	.login-card h2 {
		margin: 0;
		font-size: 1.5rem;
		text-align: center;
	}

	.error-text {
		color: #ef4444;
		font-size: 0.9rem;
		margin-top: 0.5rem;
		text-align: center;
	}

	.input-grid {
		display: flex;
		flex-direction: column;
		gap: 1rem;
	}

	.text-input {
		width: 100%;
	}

	.input-wrap {
		display: flex;
		align-items: center;
		border-radius: 0.9rem;
		border: 1px solid rgba(150, 165, 186, 0.4);
		background: rgba(255, 255, 255, 0.6);
		padding-right: 0.25rem;
	}

	.input-wrap .text-input {
		border: none;
		background: transparent;
		padding: 0.75rem 1rem;
		flex: 1;
	}

	.toggle-visibility {
		border: none;
		background: transparent;
		color: #0a27bb;
		font-weight: 600;
		cursor: pointer;
		padding: 0 0.8rem;
	}

	.input-grid label {
		display: flex;
		flex-direction: column;
		gap: 0.35rem;
		font-size: 0.9rem;
		color: #111111;
	}

	.input-grid input {
		border-radius: 0.9rem;
		border: 1px solid rgba(148, 163, 184, 0.4);
		background: rgba(255, 255, 255, 0.6);
		padding: 0.75rem 1rem;
		color: #000000;
		font-size: 0.95rem;
	}

	.actions {
		display: flex;
		justify-content: center;
	}

	.primary-action {
		border: none;
		border-radius: 999px;
		padding: 0.8rem 1.6rem;
		font-weight: 800;
		cursor: pointer;
		background: linear-gradient(120deg, #070bdd, #070bdd);
		color: #f7f7f7;
		min-width: 180px;
		text-align: center;
		font-size: 0.9rem;
	}

	.label-text {
		margin-left: 0.5rem;
		font-weight: 500;
	}
</style>
