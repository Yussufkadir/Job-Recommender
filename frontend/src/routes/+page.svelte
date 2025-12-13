<script lang="ts">
  import HeroSection from "$lib/components/HeroSection.svelte";
  import type { PageData } from "./$types";

  export let data: PageData;
</script>
<div class="home-shell">

  <nav class="nav-overlay">
    <a class="cta-button login" href="/login">Login</a>
    <a class="cta-button signup" href="/signup">Sign Up</a>
  </nav>

  <HeroSection content={data.hero} />
</div>

<style>
  .home-shell {
    position: relative;
    min-height: 100vh;
    overflow-x: hidden; 
  }

  .nav-overlay {
    position: fixed;
    top: 1.5rem;
    right: 2rem;
    display: flex;
    gap: 1rem; 
    z-index: 100; 
  }

  .cta-button {
    padding: 0.6rem 1.4rem;
    border-radius: 999px;
    text-decoration: none;
    font-weight: 600;
    backdrop-filter: blur(8px);
    transition: transform 0.2s, box-shadow 0.2s;
    font-size: 0.95rem;
  }

  .cta-button:hover {
    transform: translateY(-2px);
    box-shadow: 0 10px 20px rgba(0, 0, 0, 0.2);
  }

  .login {
    background: rgba(15, 23, 42, 0.6);
    color: #f8fafc;
    border: 1px solid rgba(148, 163, 184, 0.3);
  }

  .signup {
    background: linear-gradient(135deg, #6366f1, #a855f7);
    color: white;
    border: 1px solid rgba(255, 255, 255, 0.1);
  }

  @media (max-width: 600px) {
    .nav-overlay {
      right: 1rem;
      top: 1rem;
      gap: 0.5rem;
    }
    .cta-button {
      padding: 0.5rem 1rem;
      font-size: 0.85rem;
    }
  }
</style>