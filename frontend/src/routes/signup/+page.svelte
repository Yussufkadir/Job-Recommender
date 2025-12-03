<script lang="ts">

    const authProviders = [
        { name: "Gmail", key: "gmail", icon: "✉️" },
        { name: "GitHub", key: "github", icon: "🐙" }
    ];
    let showPassword = false;
    let email = ""
    let password = ""
    let repeatPassword = ""
    let errorMessage = ""

    async function handleAccountCreate() {
        errorMessage = ""

        if (password != repeatPassword) {
            errorMessage = "Passwords do not match !";
            return
        }

        try{
            const response = await fetch("http://localhost:8000/auth/signup", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email, password })
            });

            const data = await response.json();

            if (response.ok) {
                window.location.href = "/login";
            } else {
                errorMessage = data.detail || "Signup failed";
            }
        } catch (error) {
            console.error("Error:", error);
            errorMessage = "Could not connect to server.";
        }
    }

    function handleSocialLogin(key: string){
        if (key === 'gmail') {
            window.location.href = "http://localhost:8000/auth/google/login";
        } else if (key === 'github'){
            window.location.href = "http://localhost:8000/auth/github/login"
        }
    }
</script>

<svelte:head>
  <title>Sign Up Page</title>
</svelte:head>

<section class="page-shell">
<section class="signup-card">
    <header>
        <h2>Please sign up to the platform</h2>
    </header>

    <form class="signup-grid" on:submit|preventDefault={handleAccountCreate}>
        <label>
            Email
            <div class="input-wrap">
                <input class="text-input" type="text" placeholder="Email" bind:value={email} required/>
            </div>
        </label>
        <label>
            Password
            <div class="input-wrap">
                <input class="text-input"
                type={showPassword ? "text" : "password"} 
                placeholder="*******"
                bind:value={password}
                required
                />
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
                placeholder="*******" 
                bind:value={repeatPassword}
                required/>
                <button 
                type="button" 
                class="toggle-visibility" 
                on:click={() => (showPassword = !showPassword)}>
                    {showPassword ? "Hide" : "Show"}
                </button>
            </div>
        </label>
        <div class="actions">
            <button type="submit" class="primary-action">Sign up</button>
        </div>
    </form>


    <div style="text-align: centerl margin-top: 1rem;">
        <a href="/login" style="color: #a5b4fc; text-decoration: none; font-size: 0.9rem;">Already have an account? Log in</a>
    </div>

    <div class="social-login">
        <p>Or continue with</p>
        <div class="social-buttons">
            {#each authProviders as provider}
                <button type="button" class={`social-button ${provider.key}`} on:click={() => handleSocialLogin(provider.key)}>
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