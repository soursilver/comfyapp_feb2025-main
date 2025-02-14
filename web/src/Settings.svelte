<script>
    import { createEventDispatcher } from "svelte"; // Add this import
    const dispatch = createEventDispatcher();      // Create dispatcher
  
    export let currentAddress = "";
    export let className = "";
  
    let newAddress = currentAddress;
    let saving = false;
  
    function handleSave() {
      if (!newAddress.trim()) return;
  
      saving = true;
      dispatch("save", newAddress); // Use Svelte's dispatch
      setTimeout(() => {
        saving = false;
      }, 1000);
    }
  </script>

<div class="fixed inset-0 flex items-center justify-center z-50 p-8">
  <div class="bg-base-100 shadow-xl p-6 rounded-md">
    <h2 class="text-xl font-bold mb-4">Server Settings</h2>
    <div class="form-control">
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
    <div class="mt-6">
      <button
        on:click={handleSave}
        class="btn btn-primary w-full"
        disabled={saving}
      >
        {saving
          ? '<span class="loading loading-spinner"></span> Saving...'
          : "Save"}
      </button>
    </div>
  </div>
</div>
