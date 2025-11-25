<script lang="ts">
    const authProviders = [
        { name: "Gmail", key: "gmail", icon: "✉️" },
        { name: "GitHub", key: "github", icon: "🐙" }
    ];
    let showPassword = false;
</script>

<svelte:head>
  <title>Sign Up Page</title>
</svelte:head>

<section class="page-shell">
<section class="signup-card">
    <header>
        <h2>Please sign up to the platform</h2>
    </header>

    <form class="signup-grid">
        <label>
            Email
            <div class="input-wrap">
                <input class="text-input" type="text" placeholder="Email" />
            </div>
        </label>
        <label>
            Password
            <div class="input-wrap">
                <input class="text-input"
                type={showPassword ? "text" : "password"} 
                placeholder="*******" />
                <button 
                type="button" 
                class="toggle-visibility" 
                on:click={() => (showPassword = !showPassword)}>
                    {showPassword ? "Hide" : "Show"}
                </button>
            </div>
        </label>
        <label>
            Repeat Password
            <div class="input-wrap">
                <input class="text-input"
                type={showPassword ? "text" : "password"} 
                placeholder="*******" />
                <button 
                type="button" 
                class="toggle-visibility" 
                on:click={() => (showPassword = !showPassword)}>
                    {showPassword ? "Hide" : "Show"}
                </button>
            </div>
        </label>
    </form>

    <div class="actions">
        <button type="button" class="primary-action">Log in</button>
    </div>

    <div class="social-login">
        <p>Or continue with</p>
        <div class="social-buttons">
            {#each authProviders as provider}
                <button type="button" class={`social-button ${provider.key}`}>
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
        background: radial-gradient(circle at top, rgba(99,102,241,.15), transparent 60%);
    }

    .signup-card{
        max-width: 640px;
        margin: 2rem auto;
        padding: 1.75rem;
        border-radius: 1.5rem;
        background: rgba(15, 23, 42, 0.85);
        border: 1px solid rgba(99, 102, 241, 0.35);
        color: #f8fafc;
        display: flex;
        flex-direction: column;
        gap: 1.25rem;
    }

    .signup-card h2 {
        margin: 0;
        font-size: 1.5rem;
    }

    .input-grid {
        display: flex;
        flex-direction: column;
        gap: 1rem;
    }

    .text-input {
        width: 100%;
    }

    .input-wrap{
        display: flex;
        align-items: center;
        border-radius: 0.9rem;
        border: 1px solid rgba(148, 163, 184, 0.4);
        background: rgba(15,23,42,0.6);
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
        color: #a5b4fc;
        font-weight: 600;
        cursor: pointer;
        padding: 0 0.8rem;
    }

    .signup-grid label {
        display: flex;
        flex-direction: column;
        gap: 0.35rem;
        font-size: 0.9rem;
        color: #cbd5f5;
    }


    .signup-grid input {
        border-radius: 0.9rem;
        border: 1px solid rgba(148, 163, 184, 0.4);
        background: rgba(15, 23, 42, 0.6);
        padding: 0.75rem 1rem;
        color: #f8fafc;
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
        font-weight: 600;
        cursor: pointer;
        background: linear-gradient(120deg, #6366f1, #a855f7);
        color: #e0e7ff;
        min-width: 180px;
        text-align: center;
    }

    .social-login {
        text-align: center;
        display: flex;
        flex-direction: column;
        gap: 0.9rem;
    }

    .social-login p {
        margin: 0;
        color: #cbd5f5;
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
        background: rgba(15, 23, 42, 0.65);
        color: #f8fafc;
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