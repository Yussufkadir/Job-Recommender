<script lang="ts">
	type HeroContent = {
		title: string;
		subtitle: string;
		cta: {
			label: string;
			href: string;
		};
	};

	export let content: HeroContent;
</script>

<section class="hero">
	<div class="hero__text">
		<p class="pill">Smart job matching</p>
		<h1>{content.title}</h1>
		<p class="subtitle">{content.subtitle}</p>
		<div class="actions">
			<a class="cta" href={content.cta.href}>{content.cta.label}</a>
		</div>
	</div>
</section>

<style>
	.hero {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
		gap: 2.5rem;
		align-items: center;
		padding: clamp(3rem, 6vw, 6rem);
		min-height: 80vh;
	}

	.hero__text h1 {
		font-size: clamp(2.5rem, 5vw, 3.5rem);
		margin-bottom: 1rem;
	}

	.subtitle {
		font-size: 1.1rem;
		color: #64748b;
		max-width: 40ch;
	}

	.pill {
		display: inline-flex;
		padding: 0.35rem 0.75rem;
		border-radius: 999px;
		border: 1px solid rgba(16, 40, 221, 0.662);
		text-transform: uppercase;
		letter-spacing: 0.08em;
		font-size: 0.75rem;
		margin-bottom: 1.15rem;
	}

	.actions {
		margin-top: 1.5rem;
		display: flex;
		gap: 1rem;
		flex-wrap: wrap;
	}

	.cta,
	.secondary {
		border-radius: 999px;
		padding: 0.85rem 1.75rem;
		font-weight: 600;
		border: none;
		cursor: pointer;
		text-decoration: none;
	}

	.cta {
		background: linear-gradient(135deg, #0e11ee, #112a60);
		color: white;
		box-shadow: 0 20px 40px rgba(99, 102, 241, 0.35);
	}

	.secondary {
		background: transparent;
		border: 1px solid rgba(9, 59, 211, 0.781);
		color: inherit;
	}

	.cta:hover,
	.secondary:hover {
		opacity: 0.9;
	}

	.stats {
		list-style: none;
		margin: 0;
		padding: 0;
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
		gap: 1rem;
	}

	@media (max-width: 600px) {
		.actions {
			flex-direction: column;
		}
	}
</style>
