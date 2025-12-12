<script lang="ts">
    import { getRecommendations, type Job } from '$lib/api'
    let cvText = "";
    let skillsInput = "";
    let jobs: Job[] = [];
    let loading = false;
    let error = "";

    async function handleSearch() {
        if (!cvText || !skillsInput) {
            error = "Please fill in both CV content and Skills.";
            return;
        }

        loading = true;
        error = "";
        jobs = [];

        const skillsArray = skillsInput.split(',').map(s => s.trim()).filter(s => s.length > 0);

        try{
            const response = await getRecommendations(cvText, skillsArrays);
            jobs = respnose.jobs;
        } catch (err) {
            console.error(err);
            error = "Failed to fetch jobs. Check the backend."
        } finally {
            loading = false;
        }
    }
</script>
<svelte:head>
    <title>Main Page</title>
</svelte:head> 

<div class="page-container">
    <section class="input-section">
        <div class="glass-card">
            <h1>Job Recommender</h1>
            <p class="subtitle">Upload your CV and skills to find the jobs that fit you.</p>

            <div class="form-group">
                <label for="cv">CV Content</label>
                <textarea
                    id="cv"
                    bind:value={cvText}
                    placeholder="Paste your CV text here..."
                    rows="8"
                ></textarea>
            </div>

            <div class="form-group">
                <label for="skills">Skills (comma seperated)</label>
                <input
                    id="skills"
                    type="text"
                    bind:value={skillsInput}
                    placeholder="e.g. Python, React, SQL"
                />
            </div>

            {#if error}
                <p class="error-msg">{error}</p>
            {/if}

            <button class="search-btn" on:click={handleSearch} disabled={loading}>
                {#if loading}
                    <span class="loader"></span> Searching...
                {:else}
                    Find Matches
                {/if}
                </button>
        </div>
    </section>

    <section class="results-section">
        {#if jobs.length > 0}
        <h2>Top Recommendations</h2>
        <div class="jobs-grid">
            {#each jobs as job}
                <div class="job-card">
                    <div class="job-header">
                        <h3>{job.title}</h3>
                        <span class="score-badge" style="background: {job.match_score > 70 ? '#10b981' : '#f59e0b'}">
                            {job.match_score}% Match
                        </span>
                    </div>
                    <p class="company">{job.company} * {job.location}</p>
                    <p class="description">{job.description.slice(0, 150)}...</p>

                    <div class="actions">
                        <a href={job.link} target="_blank" class="apply-link">View Job</a>
                        <button class="tailor-btn">Tailor CV</button>
                    </div>
                </div>
            {/each}
        </div>
     {:else if !loading && !error}
        <div class="empty-state">
            <p>Jobs will appear here after you search.</p>
        </div>
      {/if}
    </section>
</div>

<style>
    :global(body) {
        font-family: "Inter", "sans-herif";
        margin: 0;
        background: #0f172a;
        background: radial-gradient(circle at top, #1e293b 0%, #020617 100%);
        color: #f8fafc;
    }

    .page-container {
        display: flex;
        min-height: 100vh;
        padding: 2rem;
        gap: 2rem;
        max-width: 1400px;
        margin: 0 auto;
    }

    .input-section {
        flex: 1;
        max-width: 450px;
    }

    .glass-card {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255,255,255,0.1);
        padding: 2rem;
        border-radius: 16px;
        box-shadow: 0 4px 30px rgba(0, 0, 0, 0.1);
    }   

    h1 {
       margin-top: 0;
       font-size: 1.8rem; 
       background: linear-gradient(90deg, #818cf8, #c084fc);
       -webkit-background-clip: text;
       background-clip: text;
       -webkit-text-fill-color: transparent;
       color: transparent;
    }
    .subtitle {
        color: #94a3b8;
        margin-bottom: 1.5rem;
        font-size: 0.9rem;
    }

    .form-group {
        margin-bottom: 1.5rem;
    }
    label {
        display: block;
        margin-bottom: 0.5rem;
        font-weight: 500;
        color: #cbd5e1;
    }

    textarea, input {
        width: 100%;
        background: rgba(0,0,0,0.3);
        border: 1px solid #334155;
        border-radius: 8px;
        padding: 0.75rem;
        color: white;
        font-family: inherit;
        box-sizing: border-box;
    }

    textarea:focus, input:focus {
        outline: 2px solid #6366f1;
        border-color: transparent;
    }

    .search-btn {
        width: 100%;
        padding: 1rem;
        background: #6366f1;
        color: white;
        border: none;
        border-radius: 8px;
        font-weight: 600;
        cursor: pointer;
        transition: background 0.2s;
    }

    .search-btn:hover {
        background: #4f46e5;
    }

    .search-btn:disabled {
        background: #475569;
        cursor: not-allowed;
    }

    .error-msg {
        color: #ef4444;
        font-size: 0.9rem;
        margin-bottom: 1rem;
        }
    

    .results-section {
        flex: 2;
        overflow-y: auto;
    }

    .jobs-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
        gap: 1.5rem;
    }

    .job-card {
        background: rgba(30, 41, 59, 0.7);
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 1.5rem;
        transition: transform 0.2s;
        }

    .job-card:hover{
        transform: translateY(-4px);
        border-color: #6366f1;
    }

    .job-header {
        display: flex;
        justify-content: space-between;
        align-items: start;
        margin-bottom: 0.5rem;
    }

    .job-header h3 {
        margin: 0;
        font-size: 1.1rem;
        color: #f1f5f9;
    }

    .score-badge {
        font-size: 0.75rem;
        padding: 0.25rem 0.5rem;
        border-radius: 99px;
        color: #020617;
        font-weight: 700;
    }

    .company {
        color: #94a3b8;
        font-size: 0.9rem;
        margin-bottom: 1rem;
    }

    .description {
        color: #cbd5e1;
        font-size: 0.9rem;
        line-height: 1.5;
        margin-bottom: 1.5rem;
    }

    .actions {
        display: flex;
        gap: 1rem;
    }

    .apply-link {
        flex: 1;
        text-align: center;
        padding: 0.5rem;
        border: 1px solid #475569;
        border-radius: 6px;
        color: white;
        text-decoration: none;
        font-size: 0.9rem;
    }

    .apply-link:hover { background: #334155;}

    .tailor-btn {
        flex: 1;
        background: rgba(99, 102, 241, 0.2);
        color: #818cf8;
        border: 1px solid rgba(99, 102, 241, 0.3);
        border-radius: 6px;
        cursor: pointer;
        font-weight: 600;
    }

    .tailor-btn:hover { background: rgba(99, 102, 241, 0.3); }
    
    .empty-state {
        height: 100%;
        display: flex;
        align-items: center;
        justify-content: center;
        color: #64748b;
        border: 2px dashed #334155;
        border-radius: 16px;
    }

    @media (max-width: 768px) {
        .page-container {flex-direction: column; }
        .input-section { max-width: 100%; }
    }
</style>