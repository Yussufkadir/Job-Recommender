<script lang="ts">
    let upload = ""
</script>
<svelte:head>
    <title>Main Page</title>
</svelte:head>

<section class="main-page">
    <section class="cv_upload">
        <form class="cv-upload-box">
            <h2>Upload CV</h2>
        </form>
    </section>
</section>

<style>
    :global(body) {
    font-family: "Inter", system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    margin: 0;
    background: radial-gradient(circle at top, #101828 0%, #05060a 60%);
    color: #f8fafc;
    }
    .main-page {
        min-height: 100vh;
        width: 100%;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 2rem;
        box-sizing: border-box;
        background: radial-gradient(circle at top, rgba(99,102,241,.15), transparent 60%);
    }
</style>