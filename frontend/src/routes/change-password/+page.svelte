<script lang="ts">
	import { API_BASE } from '$lib/api';
	import { authFetch } from '$lib/auth';

	let oldPassword = '';
	let newPassword = '';
	let confirmPassword = '';
	let message = '';
	let error = '';
	let loading = false;

	async function handleChangePassword() {
		if (newPassword !== confirmPassword) {
			error = 'New passwords do not match';
			return;
		}

		loading = true;
		message = '';
		error = '';

		try {
			const res = await authFetch(`${API_BASE}/auth/change-password`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					old_password: oldPassword,
					new_password: newPassword
				})
			});

			const data = await res.json();

			if (res.ok) {
				message = 'Password changed successfully!';
				oldPassword = '';
				newPassword = '';
				confirmPassword = '';
			} else {
				error = data.detail || 'Change failed';
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
	<title>Change Password</title>
</svelte:head>

<div class="page-container">
	<div class="card">
		<h2>Change Password</h2>

		<form on:submit|preventDefault={handleChangePassword}>
			<div class="form-group">
				<label for="old-password">Current Password</label>
				<input
					type="password"
					id="old-password"
					bind:value={oldPassword}
					required
					placeholder="********"
				/>
			</div>

			<div class="form-group">
				<label for="new-password">New Password</label>
				<input
					type="password"
					id="new-password"
					bind:value={newPassword}
					required
					placeholder="********"
				/>
				<p class="help-text">Min 8 chars, 1 uppercase, 1 digit, 1 special char</p>
			</div>

			<div class="form-group">
				<label for="confirm-password">Confirm New Password</label>
				<input
					type="password"
					id="confirm-password"
					bind:value={confirmPassword}
					required
					placeholder="********"
				/>
			</div>

			{#if message}
				<div class="success-msg">{message}</div>
			{/if}

			{#if error}
				<p class="error-msg">{error}</p>
			{/if}

			<button type="submit" disabled={loading}>
				{loading ? 'Updating...' : 'Update Password'}
			</button>
		</form>
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
		margin: 0 0 1.5rem 0;
		color: #1f2937;
		text-align: center;
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

	.help-text {
		font-size: 0.75rem;
		color: #6b7280;
		margin-top: 0.25rem;
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
		margin-top: 0.5rem;
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
		color: #065f46;
		padding: 0.75rem;
		border-radius: 6px;
		margin-bottom: 1rem;
		text-align: center;
	}
</style>
