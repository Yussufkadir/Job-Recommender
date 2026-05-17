<script lang="ts">
	import { goto } from '$app/navigation';
	import { API_BASE } from '$lib/api';
	import { setToken } from '$lib/auth';
	let showPassword = false;
	let email = '';
	let password = '';
	let repeatPassword = '';
	let errorMessage = '';
	let loading = false;

	async function handleAccountCreate() {
		errorMessage = '';

		if (password != repeatPassword) {
			errorMessage = 'Passwords do not match !';
			return;
		}

		loading = true;

		try {
			const signupRes = await fetch(`${API_BASE}/auth/signup`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ email, password })
			});

			const signupData = await signupRes.json();

			if (!signupRes.ok) {
				errorMessage = signupData.detail || 'Signup failed';
				loading = false;
				return;
			}

			const loginRes = await fetch(`${API_BASE}/auth/login`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ email, password })
			});

			if (loginRes.ok) {
				const loginData = await loginRes.json();
				setToken(loginData.access_token);
				goto('/main_page');
			} else {
				goto('/login');
			}
		} catch (error) {
			console.error('Error:', error);
			errorMessage = 'Could not connect to server.';
		} finally {
			loading = false;
		}
	}
</script>

<svelte:head>
	<title>Create Account | Job Recommender</title>
</svelte:head>

<section class="page-shell">
	<section class="signup-card">
		<header>
			<h2>Create your job search workspace</h2>
			<p class="helper-copy">Use an email and a strong password to get started.</p>
		</header>

		<form class="signup-grid" on:submit|preventDefault={handleAccountCreate}>
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
			<label>
				<span class="label-text">Repeat Password</span>
				<div class="input-wrap">
					<input
						class="text-input"
						type={showPassword ? 'text' : 'password'}
						placeholder="*******"
						bind:value={repeatPassword}
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

			{#if errorMessage}
				<p class="error-text">{errorMessage}</p>
			{/if}

			<div class="actions">
				<button type="submit" class="primary-action" disabled={loading}>
					{loading ? 'Creating account...' : 'Sign up'}
				</button>
			</div>
		</form>

		<div style="text-align: center; margin-top: 1rem;">
			<a href="/login" style="color: #a5b4fc; text-decoration: none; font-size: 0.9rem;">
				Already have an account? Log in
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
		background: radial-gradient(circle at top, rgb(252, 252, 252), transparent 60%);
	}

	.signup-card {
		max-width: 640px;
		margin: 2rem auto;
		padding: 1.75rem;
		border-radius: 1.5rem;
		background: rgba(255, 255, 255, 0.85);
		border: 1px solid rgba(99, 102, 241, 0.35);
		color: #000000;
		display: flex;
		flex-direction: column;
		gap: 1.25rem;
	}

	.signup-card h2 {
		margin: 0;
		font-size: 1.5rem;
		text-align: center;
	}

	.helper-copy {
		margin: 0.5rem 0 0;
		text-align: center;
		color: #475569;
		font-size: 0.95rem;
	}

	.error-text {
		color: #ef4444;
		font-size: 0.9rem;
		margin-top: 0.5rem;
		text-align: center;
	}

	.text-input {
		width: 100%;
	}

	.input-wrap {
		display: flex;
		align-items: center;
		border-radius: 0.9rem;
		border: 1px solid rgba(32, 63, 222, 0.692);
		background: rgb(248, 248, 248);
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
		color: #0e26a0;
		font-weight: 600;
		cursor: pointer;
		padding: 0 0.8rem;
	}

	.signup-grid {
		display: flex;
		flex-direction: column;
		gap: 1.25rem;
	}

	.signup-grid label {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
		font-size: 0.9rem;
		color: #090909;
	}

	.label-text {
		margin-left: 0.5rem;
		font-weight: 500;
	}

	.signup-grid input {
		border-radius: 0.9rem;
		border: 1px solid rgba(148, 163, 184, 0.4);
		background: rgb(244, 244, 245);
		padding: 1.5rem 1rem;
		color: #000000;
		font-size: 0.95rem;
	}

	.actions {
		display: flex;
		justify-content: center;
		margin-top: 1.5rem;
	}

	.primary-action {
		border: none;
		border-radius: 999px;
		padding: 1.1rem 1.6rem;
		font-weight: 800;
		cursor: pointer;
		background: linear-gradient(120deg, #0a0dbd, #1b0475);
		color: #e0e7ff;
		min-width: 180px;
		text-align: center;
		font-size: 0.95rem;
	}

	.primary-action:disabled {
		opacity: 0.7;
		cursor: not-allowed;
	}
</style>
