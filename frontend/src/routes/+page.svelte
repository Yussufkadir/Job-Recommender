<script lang="ts">
  import HeroSection from "$lib/components/HeroSection.svelte";
  import type { PageData } from "./$types";

  export let data: PageData;
</script>
<div class="home-shell">
  <a class="loading-cta" href="/login">Login</a>
  <HeroSection content={data.hero} />
</div>
<div class="home-shell">
    <a class="signup-cta" href="/signup">Sign Up</a>
    <HeroSection content={data.hero}/>
</div>
<style>
  .home-shell {
    position: relative;
    min-height: 100vh;
  }

  .loading-cta {
    position: fixed;
    top: 1.25rem;
    right: 6.5rem;
    background: rgba(15, 23, 42, 0.8);
    color: #f8fafc;
    padding: 0.6rem 1.4rem;
    border-radius: 999px;
    text-decoration: none;
    font-weight: 600;
    border: 1px solid rgba(148, 163, 184, 0.4);
    backdrop-filter: blur(8px);
    transition: transform 150ms ease, box-shadow 150ms ease;
  }

  .loading-cta:hover {
    transform: translateY(-1px);
    box-shadow: 0 10px 24px rgba(15, 23, 42, 0.35);
  }

  .signup-cta {
    position: fixed;
    top: 1.25rem;
    right: 0.1rem;
    background: linear-gradient(135deg, #6366f1, #a855f7);
    color: #f8fafc;
    padding: 0.5rem 1.0rem;
    border-radius: 999px;
    text-decoration: none;
    font-weight: 600;
    border: 1px solid rgba(148, 163, 184, 0.4);
    backdrop-filter: blur(8px);
    transition: transform 150ms ease, box-shadow 150ms ease;
  }

  .signup-cta:hover {
    transform: translateY(-1px);
    box-shadow: 0 10px 24px rgba(15, 23, 42, 0.35);
  }


  @media (max-width: 600px) {
    .loading-cta {
      top: 0.85rem;
      right: 1rem;
      font-size: 0.9rem;
    }
    .signup-cta {
      top: 0.65rem;
      right: 2rem;
      font-size: 0.9rem;
    }
  }
</style>