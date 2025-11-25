<script lang="ts">
  type HeroContent = {
    title: string;
    subtitle: string;
    cta: {
      label: string;
      href: string;
    };
    highlights?: Array<{
      label: string;
      value: string;
    }>;
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
      <button type="button" class="secondary">View demo</button>
    </div>
  </div>

  {#if content.highlights?.length}
    <ul class="stats">
      {#each content.highlights as stat}
        <li>
          <strong>{stat.value}</strong>
          <span>{stat.label}</span>
        </li>
      {/each}
    </ul>
  {/if}
</section>

<style>
  :global(body) {
    font-family: "Inter", system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    margin: 0;
    background: radial-gradient(circle at top, #101828 0%, #05060a 60%);
    color: #f8fafc;
  }

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
    color: #cbd5f5;
    max-width: 40ch;
  }

  .pill {
    display: inline-flex;
    padding: 0.35rem 0.75rem;
    border-radius: 999px;
    border: 1px solid rgba(255, 255, 255, 0.2);
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
    transition: transform 150ms ease, box-shadow 150ms ease;
  }

  .cta {
    background: linear-gradient(135deg, #6366f1, #a855f7);
    color: white;
    box-shadow: 0 20px 40px rgba(99, 102, 241, 0.35);
  }

  .secondary {
    background: transparent;
    border: 1px solid rgba(248, 250, 252, 0.4);
    color: inherit;
  }

  .cta:hover,
  .secondary:hover {
    transform: translateY(-1px);
  }

  .stats {
    list-style: none;
    margin: 0;
    padding: 0;
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
    gap: 1rem;
  }

  .stats li {
    background: rgba(15, 23, 42, 0.6);
    border: 1px solid rgba(99, 102, 241, 0.35);
    border-radius: 1rem;
    padding: 1.5rem;
    text-align: center;
    backdrop-filter: blur(8px);
  }

  .stats strong {
    display: block;
    font-size: 1.75rem;
    margin-bottom: 0.25rem;
  }

  .stats span {
    font-size: 0.9rem;
    color: #cbd5f5;
  }

  @media (max-width: 600px) {
    .actions {
      flex-direction: column;
    }
  }
</style>
