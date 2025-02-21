<script>
  import { onMount } from "svelte";
  import MainForm from "./MainForm.svelte";
  import Settings from "./Settings.svelte";

  let serverAddress = "http://127.0.0.1:8188";
  let useCkptModels = false; // Add state
  let showSettings = false;

  function toggleSettings() {
    showSettings = !showSettings;
  }

  function handleSave(event) {
    serverAddress = event.detail.address;
    useCkptModels = event.detail.useCkpt;
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
        useCkptModels={useCkptModels}
        className="z-20"
      />
    {/if}
    <MainForm 
      {serverAddress} 
      {useCkptModels} 
      key={serverAddress + useCkptModels}
    />
  </main>
</div>