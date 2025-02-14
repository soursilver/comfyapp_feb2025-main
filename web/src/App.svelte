<script>
  import { onMount } from "svelte";
  import MainForm from "./MainForm.svelte";
  import Settings from "./Settings.svelte";

  let serverAddress = "http://localhost:8188";
  let showSettings = false;

  function toggleSettings() {
    showSettings = !showSettings;
  }

  function handleSave(event) {
    // Extract new address from event detail
    serverAddress = event.detail;
    showSettings = false;
  }
</script>

<div class="container">
  <main class="px-4 py-6">
    <nav>
      <button on:click={toggleSettings} class="btn btn-outline mr-2">
        Settings
      </button>
    </nav>
    {#if showSettings}
      <div class="fixed inset-0 bg-black/50 z-10"></div>
      <Settings
        on:save={handleSave}
        currentAddress={serverAddress}
        className="z-20"
      />
    {/if}
    <MainForm {serverAddress} key={serverAddress} />
    <!-- Add key prop -->
  </main>
</div>
