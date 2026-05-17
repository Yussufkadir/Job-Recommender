<script lang="ts">
	const steps = [
		{
			title: 'Upload resumes',
			description:
				'Drop in your resume or connect LinkedIn to build a skills fingerprint in seconds.',
			icon: '📤'
		},
		{
			title: 'Enrich with AI',
			description:
				'We expand sparse bullet points with inferred competencies, seniority, and intent.',
			icon: '🧠'
		},
		{
			title: 'Match to live roles',
			description:
				'A ranking model compares candidate fingerprints to fresh job data across the web.',
			icon: '🎯'
		},
		{
			title: 'Share curated shortlists',
			description: 'One click exports tailored recommendations to recruiters or hiring managers.',
			icon: '📬'
		}
	];
</script>

<svelte:head>
	<title>How Job Recommender Works</title>
</svelte:head>

<main class="page">
	<header class="lead">
		<p class="eyebrow">Inside the platform</p>
		<h1>From resume to relevant role in four steps</h1>
		<p>
			Job Recommender blends resume parsing, skill inference, and personalized scoring so you can
			see the right openings faster. Here is what happens when you tap the primary call-to-action.
		</p>
	</header>

	<section class="timeline">
		{#each steps as step, index (step.title)}
			<article class="card">
				<div class="icon" aria-hidden="true">{step.icon}</div>
				<div>
					<p class="step">Step {index + 1}</p>
					<h2>{step.title}</h2>
					<p>{step.description}</p>
				</div>
			</article>
		{/each}
	</section>

	<section class="cta">
		<div>
			<h3>Ready to see tailored matches?</h3>
			<p>
				Sign up for early access and receive curated suggestions powered by the same workflow
				described above.
			</p>
		</div>
		<div class="cta__actions">
			<a class="primary" href="/">Back to home</a>
			<button type="button" class="secondary">Request demo</button>
		</div>
	</section>
</main>

<style>
	.page {
		min-height: 100vh;
		padding: clamp(2.5rem, 6vw, 5rem) clamp(1.5rem, 5vw, 6rem);
		display: flex;
		flex-direction: column;
		gap: 3rem;
	}

	.lead h1 {
		font-size: clamp(2.25rem, 5vw, 3.5rem);
		margin: 0.5rem 0 1rem;
	}

	.lead p {
		max-width: 65ch;
		color: #cbd5f5;
		line-height: 1.6;
	}

	.eyebrow {
		text-transform: uppercase;
		letter-spacing: 0.1em;
		font-size: 0.8rem;
		color: #94a3b8;
	}

	.timeline {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
		gap: 1.5rem;
	}

	.card {
		background: rgba(15, 23, 42, 0.7);
		border: 1px solid rgba(99, 102, 241, 0.3);
		border-radius: 1.25rem;
		padding: 1.75rem;
		display: flex;
		gap: 1rem;
		align-items: flex-start;
	}

	.icon {
		width: 3rem;
		height: 3rem;
		border-radius: 0.85rem;
		background: rgba(99, 102, 241, 0.15);
		display: grid;
		place-items: center;
		font-size: 1.25rem;
	}

	.step {
		text-transform: uppercase;
		letter-spacing: 0.08em;
		font-size: 0.75rem;
		color: #94a3b8;
		margin: 0 0 0.25rem;
	}

	.card h2 {
		margin: 0 0 0.35rem;
		font-size: 1.2rem;
	}

	.card p {
		margin: 0;
		color: #cbd5f5;
	}

	.cta {
		border-radius: 1.5rem;
		border: 1px solid rgba(248, 250, 252, 0.2);
		padding: clamp(1.5rem, 4vw, 2.5rem);
		display: flex;
		justify-content: space-between;
		gap: 1.5rem;
		background: linear-gradient(135deg, rgba(99, 102, 241, 0.15), rgba(168, 85, 247, 0.15));
		flex-wrap: wrap;
	}

	.cta__actions {
		display: flex;
		gap: 1rem;
		flex-wrap: wrap;
		align-items: center;
	}

	.primary,
	.secondary {
		border-radius: 999px;
		padding: 0.85rem 1.75rem;
		font-weight: 600;
		border: none;
		cursor: pointer;
		text-decoration: none;
		color: inherit;
	}

	.primary {
		background: white;
		color: #0f172a;
	}

	.secondary {
		background: transparent;
		border: 1px solid rgba(248, 250, 252, 0.5);
	}

	@media (max-width: 600px) {
		.card {
			flex-direction: column;
		}
	}
</style>
