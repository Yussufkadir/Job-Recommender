<script lang="ts">
  import HeroSection from "$lib/components/HeroSection.svelte";
  import type { PageData } from "./$types";

  export let data: PageData;
</script>

<HeroSection content={data.hero} />