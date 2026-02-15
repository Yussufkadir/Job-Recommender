<script lang="ts">
	import { API_BASE } from '$lib/api';
	const authProviders = [
		{ name: 'Gmail', key: 'gmail', icon: '✉️' },
		{ name: 'GitHub', key: 'github', icon: '🐙' }
	];
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
				localStorage.setItem('token', data.access_token);
				window.location.href = '/main_page';
			} else {
				errorMessage = data.detail || 'Login Failed';
			}
		} catch (error) {
			console.error({ Error: error });
			errorMessage = 'Could not connect to the server.';
		}
	}

	function handleSocialLogin(key: string) {
		if (key === 'gmail') {
			window.location.href = `${API_BASE}/auth/google/login`;
		} else if (key === 'github') {
			window.location.href = `${API_BASE}/auth/github/login`;
		}
	}
</script>

<svelte:head>
	<title>Login Page</title>
</svelte:head>

<section class="page-shell">
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
					<input class="text-input" type="text" placeholder="Email" bind:value={email} required />
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
		</form>
		<div class="social-login">
			<p>Or continue with</p>
			<div class="social-buttons">
				{#each authProviders as provider}
					<button
						type="button"
						class={`social-button ${provider.key}`}
						on:click={() => handleSocialLogin(provider.key)}
					>
						<span aria-hidden="true">{provider.icon}</span>
						{provider.name}
					</button>
				{/each}
			</div>
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

	.social-login {
		text-align: center;
		display: flex;
		flex-direction: column;
		gap: 0.9rem;
	}

	.social-login p {
		margin: 0;
		color: #595a5d;
		font-size: 0.9rem;
	}

	.social-buttons {
		display: flex;
		gap: 0.75rem;
		flex-wrap: wrap;
		justify-content: center;
	}

	.social-button {
		border-radius: 0.85rem;
		border: 1px solid rgba(148, 163, 184, 0.4);
		background: rgb(246, 246, 246);
		color: #000000;
		padding: 0.6rem 1.2rem;
		display: inline-flex;
		align-items: center;
		gap: 0.45rem;
		font-weight: 600;
		cursor: pointer;
	}

	.social-button span {
		font-size: 1.1rem;
	}

	.social-button.gmail {
		border-color: rgba(244, 114, 182, 0.6);
	}

	.social-button.github {
		border-color: rgba(148, 163, 184, 0.8);
	}
</style>
