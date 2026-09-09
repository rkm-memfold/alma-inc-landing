// One flow for both the personal invite (/invite, ticket in the URL) and the
// universal link (/join/<code>, email then admit). Every outcome resolves in
// this one card: the account is created here, then the same Download button
// appears in the same place. Nothing redirects to another page.
(() => {
  const card = document.getElementById("card");
  const els = {
    readySub: document.getElementById("ready-sub"),
    download: document.getElementById("download"),
    closedTitle: document.getElementById("closed-title"),
    closedSub: document.getElementById("closed-sub"),
    form: document.getElementById("form"),
    email: document.getElementById("email"),
    submit: document.getElementById("submit"),
    err: document.getElementById("err"),
  };

  const CLOSED = {
    expired: ["This link has expired", "Ask whoever shared it for a new one."],
    full: ["This link is full", "It has admitted everyone it can. Ask for a new one."],
    unknown: ["Link not recognised", "Check the link, or ask for a new one."],
    used: ["This invitation was already used", "Get Alma below and sign in with the invited email."],
    missing: ["Invitation link incomplete", "Open the link from your email, or ask for a new one."],
    error: ["Something went wrong", "Refresh in a moment, or ask for a new link."],
  };

  const show = (state) => { card.dataset.state = state; };

  function closed(kind, detail) {
    if (detail !== undefined) console.error("alma invite:", kind, detail);
    els.closedTitle.textContent = CLOSED[kind][0];
    els.closedSub.textContent = CLOSED[kind][1];
    show("closed");
  }

  async function ready(email) {
    els.readySub.innerHTML = email
      ? "Signed in as <strong>" + email + "</strong>."
      : "Your account is ready.";
    if (!(await downloadReady)) {
      els.readySub.textContent = "The download is not reachable right now. Refresh in a moment.";
    }
    show("ready");
  }

  // Resolve the download to the build the update feed ships, served from this
  // domain. Started on load so the button is ready the moment it is shown.
  const downloadReady = (async () => {
    try {
      const response = await fetch("/appcast.xml", { cache: "no-store" });
      const feed = new DOMParser().parseFromString(await response.text(), "application/xml");
      const stable = [...feed.querySelectorAll("item")].find(
        (item) => !item.getElementsByTagName("sparkle:channel").length,
      );
      const url = stable?.querySelector("enclosure")?.getAttribute("url");
      if (!url) return false;
      els.download.href = "/download/" + new URL(url).pathname.split("/").pop();
      els.download.removeAttribute("aria-disabled");
      return true;
    } catch {
      return false;
    }
  })();

  async function consumeTicket(ticket) {
    if (typeof Clerk === "undefined") return closed("error", "clerk-js did not load");
    try {
      await Clerk.load();
    } catch (failure) {
      return closed("error", failure);
    }
    if (Clerk.user) {
      ready(Clerk.user.primaryEmailAddress?.emailAddress ?? "");
      return;
    }
    try {
      const attempt = await Clerk.client.signUp.create({ strategy: "ticket", ticket });
      if (attempt.status === "complete") {
        await Clerk.setActive({ session: attempt.createdSessionId });
        ready(attempt.emailAddress ?? "");
        return;
      }
      closed("error", attempt.status);
    } catch (refusal) {
      const code = String(refusal?.errors?.[0]?.code ?? refusal);
      if (/already|taken|exists/i.test(code)) ready("");
      else closed("used", refusal);
    }
  }

  // Join mode: email, then admit on the spot and consume the ticket here.
  function wireForm(code) {
    show("form");
    els.form.addEventListener("submit", async (event) => {
      event.preventDefault();
      els.err.textContent = "";
      els.submit.disabled = true;
      try {
        const response = await fetch("/api/join", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ code, email: els.email.value }),
        });
        if (!response.ok) throw new Error(String(response.status));
        const result = await response.json();
        if (result.outcome === "ready" && result.url) {
          show("working");
          const ticket = new URL(result.url).searchParams.get("ticket") ?? "";
          if (ticket) return consumeTicket(ticket);
          return ready("");
        }
        if (result.outcome === "have-access") return ready("");
        if (result.outcome === "bad-email") {
          els.err.textContent = "That does not look like an email address.";
          els.submit.disabled = false;
          return;
        }
        if (result.outcome in CLOSED) return closed(result.outcome);
        els.err.textContent = "That did not go through. Try again.";
        els.submit.disabled = false;
      } catch {
        els.err.textContent = "That did not go through. Try again.";
        els.submit.disabled = false;
      }
    });
  }

  const ambient = document.getElementById("ambient");
  if (ambient) {
    const art = new Image();
    const reveal = () => ambient.classList.add("lit");
    art.onload = reveal;
    art.onerror = reveal;
    art.src = "/page/alma-art-ref.png";
  }

  const here = new URL(window.location.href);
  const ticket = here.searchParams.get("__clerk_ticket");
  if (ticket) {
    show("working");
    consumeTicket(ticket);
  } else {
    const code = here.pathname.split("/").filter(Boolean).pop() ?? "";
    if (/^[0-9a-f]{16}$/.test(code)) wireForm(code);
    else closed(here.pathname.startsWith("/invite") ? "missing" : "unknown");
  }
})();
