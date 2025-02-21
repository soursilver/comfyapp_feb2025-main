<script>
  import { createEventDispatcher } from "svelte";
  const dispatch = createEventDispatcher();

  export let currentAddress = "";
  export let useCkptModels = false;
  export let className = "";

  let newAddress = currentAddress;
  let newuseCkptModels = useCkptModels;
  let saving = false;

  function handleSave() {
    if (!newAddress.trim()) return;

    saving = true;
    dispatch("save", {
      address: newAddress,
      useCkpt: newuseCkptModels,
    });
    setTimeout(() => {
      saving = false;
    }, 1000);
  }
</script>

<div class="fixed inset-0 flex items-center justify-center z-50 p-8">
  <div class="bg-base-100 shadow-xl p-6 rounded-md w-full max-w-lg">
    <h2 class="text-xl font-bold mb-4">Server Settings</h2>

    <!-- Server Address Input -->
    <div class="form-control mb-4">
      <label class="label">
        <span class="label-text font-semibold">Server Address</span>
      </label>
      <input
        type="text"
        bind:value={newAddress}
        class="input input-bordered w-full"
        placeholder="http://localhost:8188 or https://your-tunnel.com"
      />
    </div>

    <!-- Ckpt Toggle -->
    <div class="form-control">
      <label class="label cursor-pointer justify-start gap-4">
        <input
          type="checkbox"
          bind:checked={newuseCkptModels}
          class="toggle toggle-primary"
        />
        <span class="label-text">Use Checkpoint Models</span>
      </label>
    </div>

    <!-- Save Button -->
    <div class="mt-6">
      <button
        on:click={handleSave}
        class="btn btn-primary w-full"
        disabled={saving}
      >
        {#if saving}
          <span class="loading loading-spinner"></span> Saving...
        {:else}
          Save
        {/if}
      </button>
    </div>
  </div>
</div>
