<script lang="ts">
	import { API_BASE } from '$lib/api';

	let email = '';
	let message = '';
	let error = '';
	let loading = false;

	async function handleForgotPassword() {
		loading = true;
		message = '';
		error = '';

		try {
			const res = await fetch(`${API_BASE}/auth/forgot-password`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ email })
			});
			const data = await res.json();

			if (res.ok) {
				message = data.message;
			} else {
				error = data.detail || 'Request failed';
			}
		} catch (e) {
			console.error(e);
			error = 'Connection error';
		} finally {
			loading = false;
		}
	}
</script>

<svelte:head>
	<title>Forgot Password</title>
</svelte:head>

<div class="page-container">
	<div class="card">
		<h2>Reset Password</h2>
		<p class="subtitle">Enter your email to receive a password reset token.</p>

		<form on:submit|preventDefault={handleForgotPassword}>
			<div class="form-group">
				<label for="email">Email</label>
				<input type="email" id="email" bind:value={email} required placeholder="john@example.com" />
			</div>

			{#if message}
				<div class="success-msg">
					<p>{message}</p>
					<p class="hint">Please check your inbox (and spam folder) for the reset link.</p>
				</div>
			{/if}

			{#if error}
				<p class="error-msg">{error}</p>
			{/if}

			<button type="submit" disabled={loading}>
				{loading ? 'Sending...' : 'Send Reset Token'}
			</button>
		</form>

		<div class="links">
			<a href="/login">Back to Login</a>
		</div>
	</div>
</div>

<style>
	.page-container {
		min-height: 80vh;
		display: flex;
		align-items: center;
		justify-content: center;
		padding: 1rem;
	}

	.card {
		background: white;
		padding: 2rem;
		border-radius: 12px;
		box-shadow:
			0 4px 6px -1px rgba(0, 0, 0, 0.1),
			0 2px 4px -1px rgba(0, 0, 0, 0.06);
		width: 100%;
		max-width: 400px;
	}

	h2 {
		margin: 0 0 0.5rem 0;
		color: #1f2937;
		text-align: center;
	}

	.subtitle {
		color: #6b7280;
		text-align: center;
		margin-bottom: 1.5rem;
		font-size: 0.9rem;
	}

	.form-group {
		margin-bottom: 1rem;
	}

	label {
		display: block;
		font-size: 0.875rem;
		font-weight: 500;
		color: #374151;
		margin-bottom: 0.25rem;
	}

	input {
		width: 100%;
		padding: 0.75rem;
		border: 1px solid #d1d5db;
		border-radius: 6px;
		box-sizing: border-box;
	}

	input:focus {
		outline: 2px solid #2563eb;
		border-color: transparent;
	}

	button {
		width: 100%;
		padding: 0.75rem;
		background: #2563eb;
		color: white;
		border: none;
		border-radius: 6px;
		font-weight: 600;
		cursor: pointer;
		transition: background 0.2s;
	}

	button:hover {
		background: #1d4ed8;
	}

	button:disabled {
		background: #93c5fd;
		cursor: not-allowed;
	}

	.error-msg {
		color: #dc2626;
		font-size: 0.875rem;
		text-align: center;
		margin-bottom: 1rem;
	}

	.success-msg {
		background: #ecfdf5;
		border: 1px solid #10b981;
		color: #065f46;
		padding: 1rem;
		border-radius: 6px;
		margin-bottom: 1rem;
		font-size: 0.9rem;
		word-break: break-all;
	}

	.hint {
		margin-top: 0.5rem;
		font-size: 0.85rem;
		color: #047857;
	}

	.links {
		text-align: center;
		margin-top: 1.5rem;
	}

	a {
		color: #2563eb;
		text-decoration: none;
		font-size: 0.9rem;
	}

	a:hover {
		text-decoration: underline;
	}
</style>
