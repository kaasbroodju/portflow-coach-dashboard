// Portflow coach dashboard: small enhancements; every page also works without JavaScript.

(() => {
  "use strict";

  // Portflow status in the top bar (spec 003, F13 and F14) --------------------------------

  const statusEl = () => document.getElementById("portflow-status");
  const reloadWatchEl = () => document.getElementById("portflow-reload-watch");
  let fingerprint = null;
  let wasBusy = null;
  let wasFetching = null;

  function closePanelOnEscapeOrOutsideClick() {
    document.addEventListener("keydown", (event) => {
      const panel = statusEl();
      if (event.key === "Escape" && panel?.open) panel.open = false;
    });
    document.addEventListener("click", (event) => {
      const panel = statusEl();
      if (panel?.open && !panel.contains(event.target)) panel.open = false;
    });
  }

  function replace(id, html, keepOpen) {
    const old = document.getElementById(id);
    if (!old) return;
    const wasOpen = old.open;
    const template = document.createElement("template");
    template.innerHTML = html.trim();
    const fresh = id === "portflow-status" ? template.content.firstElementChild : null;
    if (fresh) {
      if (keepOpen && wasOpen) fresh.open = true;
      old.replaceWith(fresh);
    } else {
      old.innerHTML = html;
    }
  }

  async function poll() {
    let delay = 60000;
    try {
      const path = encodeURIComponent(location.pathname);
      const response = await fetch(`/portflow/status?pad=${path}`, { headers: { Accept: "application/json" } });
      const status = await response.json();
      delay = status.poll_ms;

      // "Uit Portflow kiezen" (spec 004, F5): once a login/refresh attempt that was
      // running finishes (success or failure), reload so the page shows the result
      // (the share list, or an updated message) without an extra click.
      const busyNow = status.state === "logging_in" || status.state === "refreshing";
      if (reloadWatchEl() && wasBusy === true && !busyNow) {
        location.reload();
        return;
      }
      wasBusy = busyNow;

      // Spec 005, F9: once a fetch round finishes, show the new data without a manual reload.
      if (wasFetching === true && !status.fetch_running && document.querySelector("[data-reload-after-fetch]")) {
        location.reload();
        return;
      }
      wasFetching = status.fetch_running;

      const typing = statusEl()?.contains(document.activeElement) && document.activeElement.matches("input, textarea");
      if (fingerprint !== null && status.fingerprint !== fingerprint && !typing) {
        replace("portflow-status", status.status_html, true);
        replace("portflow-banner", status.banner_html);
        replace("sidebar-user", status.user_html);
        replace("topbar-avatar", status.avatar_html);
        replace("refresh", status.refresh_html);
      }
      if (!typing) fingerprint = status.fingerprint;
    } catch {
      // The app may be restarting; try again later.
    }
    setTimeout(poll, delay);
  }

  if (statusEl()) {
    closePanelOnEscapeOrOutsideClick();
    poll();
  }

  // Spec 019, F14: on a page with a student list, "Verversen" fetches the students visible in it.
  document.addEventListener("submit", (event) => {
    const form = event.target;
    const list = document.getElementById("student-table");
    if (!form.matches("form.refresh") || !list) return;
    form.querySelectorAll("input[name=student], input[name=lijst]").forEach((el) => el.remove());
    const add = (name, value) => {
      const input = document.createElement("input");
      input.type = "hidden"; input.name = name; input.value = value;
      form.appendChild(input);
    };
    add("lijst", "1");
    list.querySelectorAll("tr[data-student-id]").forEach((row) => {
      if (!row.hidden && !row.closest(".table-group")?.hidden) add("student", row.dataset.studentId);
    });
  }, true);
})();

(() => {
  "use strict";

  // "Uit Portflow kiezen": the loading indicator that fetches the share list as an HTML
  // fragment (spec 004, F6 technical), plus search, select all/none and the submit
  // button once the list is there (F9, F11).

  function enhancePickList() {
    const list = document.getElementById("portflow-candidates");
    const submit = document.getElementById("portflow-submit");
    if (!list || !submit) return;

    const rows = () => Array.from(list.querySelectorAll(".pick-row"));
    const checkbox = (row) => row.querySelector("input[type=checkbox]");

    function visibleRows(query) {
      return rows().filter((row) => {
        const visible = !query || row.dataset.pickName.includes(query);
        row.hidden = !visible;
        return visible;
      });
    }

    // "student|studenten" by default; the Coaches and Gildemeesters pages pass their own words.
    const [single, plural] = (list.dataset.pickNoun || "student|studenten").split("|");
    const capital = (word) => word.charAt(0).toUpperCase() + word.slice(1);

    function updateSubmit() {
      const count = rows().filter((row) => checkbox(row).checked).length;
      submit.textContent = count === 0 ? `${capital(plural)} toevoegen` : `${count} ${count === 1 ? single : plural} toevoegen`;
      submit.disabled = count === 0;
    }

    const search = document.getElementById("portflow-search");
    search?.addEventListener("input", () => visibleRows(search.value.trim().toLowerCase()));

    list.addEventListener("change", (event) => {
      if (event.target.matches("input[type=checkbox]")) updateSubmit();
    });

    document.querySelectorAll("[data-pick-select]").forEach((button) => {
      button.addEventListener("click", () => {
        const checked = button.dataset.pickSelect === "all";
        visibleRows(search?.value.trim().toLowerCase() || "").forEach((row) => {
          const input = checkbox(row);
          if (!input.disabled) input.checked = checked;
        });
        updateSubmit();
      });
    });

    updateSubmit();
  }

  const loading = document.getElementById("portflow-list-loading");
  if (loading) {
    fetch(loading.dataset.fragmentUrl, { headers: { Accept: "text/html" } })
      .then((response) => {
        if (!response.ok) throw new Error("fragment fetch failed");
        return response.text();
      })
      .then((html) => {
        const template = document.createElement("template");
        template.innerHTML = html.trim();
        loading.replaceWith(template.content);
        enhancePickList();
      })
      .catch(() => {
        loading.innerHTML =
          `<p class="muted">Niet gelukt. <a href="${location.pathname}/lijst">Opnieuw proberen</a>.</p>`;
      });
  } else {
    enhancePickList();
  }
})();

(() => {
  "use strict";

  // Timeline of evaluations (spec 029, F2): show the chosen students at once; the button is for no-JS.
  const who = document.getElementById("timeline-who");
  if (!who) return;
  who.querySelectorAll("[data-js-hide]").forEach((el) => { el.hidden = true; });
  who.addEventListener("change", () => who.submit());
})();

(() => {
  "use strict";

  // Student overview (spec 001): submit filters on change (F13-F16), search while typing
  // with ⌘K (F17), sort by clicking a column header (F18) and keep the counter right (F19).

  const card = document.getElementById("student-table");
  if (!card) return;

  card.querySelectorAll(".js-hide").forEach((el) => { el.hidden = true; });

  const filters = document.getElementById("table-filters");
  filters?.addEventListener("change", (event) => {
    if (event.target.matches("select, input[type=checkbox]")) filters.submit();
  });
  filters?.addEventListener("submit", () => {
    // Do not put the (client-side) search or empty filters in the address.
    filters.querySelectorAll("select, input").forEach((el) => {
      if (el.id === "table-search" || (!el.value && el.tagName === "SELECT") || (el.type === "checkbox" && !el.checked)) {
        el.disabled = true;
      }
    });
  });

  // Spec 028: fold the filters away or show them without reloading; the state is kept (F5).
  const foldForm = document.getElementById("filters-fold");
  const foldButton = document.querySelector(".filters-toggle");
  foldButton?.addEventListener("click", (event) => {
    event.preventDefault();
    const main = document.querySelector("main.content");
    const compact = !main.classList.contains("filters-compact");
    main.classList.toggle("filters-compact", compact);
    foldButton.setAttribute("aria-expanded", String(!compact));
    foldButton.value = compact ? "uitgebreid" : "compact";
    const data = new FormData(foldForm);
    data.set("stand", compact ? "compact" : "uitgebreid");
    fetch(foldForm.action, { method: "POST", body: data, headers: { "X-Requested-With": "fetch" } });
  });

  const listColumnForm = document.getElementById("list-column-form");   // spec 010, F5
  listColumnForm?.addEventListener("change", () => listColumnForm.submit());

  const colourForm = document.getElementById("colour-form");   // F23
  colourForm?.addEventListener("change", () => colourForm.submit());

  const columnForm = document.getElementById("column-form");
  columnForm?.addEventListener("change", () => columnForm.submit());

  // Custom columns (F8): save when the field loses focus after a change, or with Enter.
  card.querySelectorAll(".custom-cell [name=waarde]").forEach((input) => {   // spec 024: also the choice list
    input.addEventListener("change", () => input.form.submit());
  });

  const table = document.getElementById("students");
  const count = document.getElementById("table-count");
  const search = document.getElementById("table-search");

  // Spec 019: small saves without reloading the overview.
  async function post(form) {
    const response = await fetch(form.action, {
      method: "POST", body: new FormData(form), headers: { "X-Requested-With": "fetch" },
    });
    if (!response.ok) throw new Error(await response.text() || "Opslaan is niet gelukt.");
    if (response.status === 205) location.reload();   // spec 025: the invulling was filled as well
    return response;
  }

  // F4, F5: hide a student, or show again. With "Alle studenten die ik niet heb verborgen"
  // the row disappears; with "Alle studenten van wie ik het portfolio kan zien" it is dimmed.
  const who = document.querySelector("#table-filters select[name=wie]");
  card.querySelectorAll(".hide-form").forEach((form) => {
    form.addEventListener("submit", (event) => {
      event.preventDefault();
      const row = form.closest(".student-row");
      const hide = form.dataset.hideAction === "hide";
      post(form).then(() => {
        if (hide && who?.value === "zichtbaar") {
          const group = row.closest(".table-group");
          row.remove();
          const header = group?.querySelector(".group-count");
          const left = group ? group.querySelectorAll(".student-row").length : 0;
          if (header) header.textContent = `${left} student${left === 1 ? "" : "en"}`;
          if (group && left === 0) group.remove();
          if (!table.querySelector(".student-row")) { location.reload(); return; }
          updateCount();
        } else {
          row.classList.toggle("is-hidden-student", hide);
        }
      }).catch((error) => alert(error.message));
    });
  });

  // Spec 022: the lists in the student list save right away. The sort value follows the choice;
  // a guild change reloads in place, because the guild master column changes along.
  card.querySelectorAll(".inline-pick select").forEach((select) => {
    select.addEventListener("change", () => {
      const form = select.form;
      post(form).then(() => {
        if (form.hasAttribute("data-reload")) { location.reload(); return; }
        // The first-name and full-name columns save the same field: keep both lists in step.
        form.closest("tr").querySelectorAll(".inline-pick").forEach((other) => {
          if (other.action !== form.action) return;
          const list = other.querySelector("select");
          list.value = select.value;
          const cell = other.closest("td");
          const text = list.value ? list.selectedOptions[0].textContent.trim().toLowerCase() : "~";
          if (cell.dataset.col === "semester") cell.dataset.sortValue = list.value || "99";
          else if (!cell.dataset.col.startsWith("guildmaster")) cell.dataset.sortValue = text;
        });
      }).catch((error) => { alert(error.message); location.reload(); });
    });
  });

  // Spec 021: make me coach or guild master; reload in place, because more cells can change.
  card.querySelectorAll(".make-me-form").forEach((form) => {
    form.addEventListener("submit", (event) => {
      event.preventDefault();
      post(form).then(() => location.reload()).catch((error) => alert(error.message));
    });
  });

  function updateCount() {
    if (!table || !count) return;
    const visible = table.querySelectorAll(".student-row:not([hidden])").length;
    count.textContent = `${visible} van ${count.dataset.total} studenten`;
  }

  search?.addEventListener("input", () => {
    const query = search.value.trim().toLowerCase();
    table?.querySelectorAll(".table-group").forEach((group) => {
      let any = false;
      group.querySelectorAll(".student-row").forEach((row) => {
        row.hidden = Boolean(query) && !row.dataset.search.includes(query);
        any = any || !row.hidden;
      });
      group.hidden = !any;
    });
    updateCount();
  });

  document.addEventListener("keydown", (event) => {
    if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k" && search) {
      event.preventDefault();
      search.focus();
      search.select();
    }
  });

  function sortValue(row, key, index) {
    if (row.dataset[`sort${key.charAt(0).toUpperCase()}${key.slice(1)}`] !== undefined) {
      return row.dataset[`sort${key.charAt(0).toUpperCase()}${key.slice(1)}`];
    }
    const cell = row.children[index];
    const value = cell?.dataset.sortValue ?? "";
    return value !== "" && !Number.isNaN(Number(value)) ? Number(value) : value;
  }

  table?.querySelectorAll("thead th[data-sort]").forEach((th, index) => {
    th.querySelector("button")?.addEventListener("click", () => {
      const ascending = th.getAttribute("aria-sort") !== "ascending";
      table.querySelectorAll("thead th").forEach((other) => other.removeAttribute("aria-sort"));
      th.setAttribute("aria-sort", ascending ? "ascending" : "descending");
      const key = th.dataset.sort.replace(/[-_]([a-z])/g, (_, c) => c.toUpperCase());
      const byData = ["name", "profile", "coach", "coachFull", "guildMaster", "guildMasterFull", "track"].includes(key);
      table.querySelectorAll(".table-group").forEach((group) => {
        const rows = Array.from(group.querySelectorAll(".student-row"));
        rows.sort((a, b) => {
          const va = sortValue(a, byData ? key : "", index);
          const vb = sortValue(b, byData ? key : "", index);
          const order = typeof va === "number" && typeof vb === "number" ? va - vb : String(va).localeCompare(String(vb), "nl");
          return (ascending ? order : -order) || a.dataset.sortName.localeCompare(b.dataset.sortName, "nl");
        });
        rows.forEach((row) => group.appendChild(row));
      });
    });
  });
})();

(() => {
  "use strict";

  // Student bewerken (spec 011, F2): show the guild that follows from the chosen primary role.
  const role = document.getElementById("primary-role");
  const guild = document.getElementById("guild-of-role");
  if (!role || !guild) return;
  role.addEventListener("change", () => {
    const option = role.options[role.selectedIndex];
    guild.textContent = option.value ? option.dataset.guild : "–";
  });
})();

(() => {
  "use strict";

  // Excel import preview (spec 013, F6): search, select all/none and the count on the button.
  const list = document.getElementById("import-rows");
  const submit = document.getElementById("import-submit");
  if (!list || !submit) return;
  const boxes = () => Array.from(list.querySelectorAll("input[data-import-new]"));
  const search = document.getElementById("import-search");

  function update() {
    const count = boxes().filter((box) => box.checked).length;
    submit.textContent = `Importeren (${count} toevoegen, ${submit.dataset.existing} bijwerken)`;
  }
  search?.addEventListener("input", () => {
    const query = search.value.trim().toLowerCase();
    list.querySelectorAll(".import-row").forEach((row) => { row.hidden = Boolean(query) && !row.dataset.search.includes(query); });
  });
  document.querySelectorAll("[data-import-select]").forEach((button) => {
    button.addEventListener("click", () => {
      boxes().forEach((box) => { if (!box.closest(".import-row").hidden) box.checked = button.dataset.importSelect === "all"; });
      update();
    });
  });
  list.addEventListener("change", update);
})();

(() => {
  "use strict";

  // Alles verwijderen (spec 014, F3): the button works only after typing the word.
  const word = document.getElementById("reset-word");
  const submit = document.getElementById("reset-submit");
  if (!word || !submit || submit.disabled) return;
  const check = () => { submit.disabled = word.value.trim().toUpperCase() !== word.dataset.word; };
  word.addEventListener("input", check);
  check();
})();

(() => {
  "use strict";

  // Student bewerken, guilds (spec 016, F4): add and remove guild rows.
  document.documentElement.classList.add("js");
  const rows = document.getElementById("guild-rows");
  if (!rows) return;
  const add = document.getElementById("guild-add");
  const all = () => Array.from(rows.querySelectorAll(".guild-row"));
  const empty = all().find((row) => row.classList.contains("is-empty"));
  const template = empty?.cloneNode(true);
  if (empty && all().length > 1) empty.remove();   // with JavaScript the extra empty row is not needed

  rows.addEventListener("click", (event) => {
    const button = event.target.closest("[data-guild-remove]");
    if (!button) return;
    const row = button.closest(".guild-row");
    if (all().length > 1) row.remove();
    else row.querySelectorAll("select").forEach((select) => { select.value = ""; });
  });
  add?.addEventListener("click", () => {
    const row = template.cloneNode(true);
    row.querySelectorAll("select").forEach((select) => { select.value = ""; });
    add.before(row);
    row.querySelector("select")?.focus();
  });
})();

(() => {
  "use strict";

  // Project form (spec 012, F11): fill the display name while typing, until the user edits it.
  const display = document.getElementById("project-display");
  if (!display) return;
  const form = display.form;
  const value = (name) => form.querySelector(`[name=${name}]`).value.trim();
  const fill = () => {
    if (display.dataset.edited) return;
    const number = value("nummer");
    const base = value("opdrachtgever") ? `${value("opdrachtgever")} - ${value("naam")}` : value("naam");
    display.value = base ? (number ? `${base} (${number.padStart(2, "0")})` : base) : "";
  };
  display.addEventListener("input", () => { display.dataset.edited = display.value ? "1" : ""; });
  ["nummer", "naam", "opdrachtgever"].forEach((name) => form.querySelector(`[name=${name}]`).addEventListener("input", fill));
})();

(() => {
  "use strict";

  // Spec 020, U3: while updating, ask the app for its version until the new one answers.
  const box = document.getElementById("updating");
  const step = document.getElementById("updating-step");
  if (!box || !step) return;
  const oldVersion = box.dataset.version;
  const attempt = box.dataset.attempt;
  const stuck = document.getElementById("updating-stuck");
  const STUCK_AFTER_MS = 3 * 60 * 1000;
  let lastAnswer = Date.now();
  const poll = async () => {
    try {
      const answer = await fetch("/versie", { cache: "no-store" }).then((r) => r.json());
      lastAnswer = Date.now();
      if (stuck) stuck.hidden = true;
      if (answer.version !== oldVersion) {
        window.location.href = "/instellingen#versie";
        return;
      }
      const failed = answer.result && answer.result.attempt === attempt && !answer.result.ok;
      if (answer.update.error || failed) {
        step.textContent = failed ? answer.result.message : answer.update.error;
        box.querySelector("h2").textContent = "Bijwerken is niet gelukt";
        return;
      }
      if (answer.update.step) step.textContent = answer.update.step;
    } catch (error) {
      step.textContent = "Opnieuw starten";   // the app is restarting: keep asking
      if (stuck && Date.now() - lastAnswer > STUCK_AFTER_MS) stuck.hidden = false;   // spec 020, U3
    }
    window.setTimeout(poll, 2000);
  };
  window.setTimeout(poll, 1500);
})();

(() => {
  "use strict";

  // Spec 034, F1: fetch the evidence of this student when the page opens, then replace the block.
  const block = document.getElementById("evidence-block");
  if (!block) return;
  const status = document.getElementById("evidence-status");
  if (status) status.textContent = "Bewijsstukken ophalen…";
  fetch(block.dataset.fetch, { method: "POST", headers: { "X-Requested-With": "fetch" } })
    .then((response) => (response.ok ? response.text() : Promise.reject(response.status)))
    .then((html) => { block.outerHTML = html; })
    .catch(() => { if (status) status.textContent = "Ophalen is niet gelukt; probeer het later opnieuw."; });
})();

(() => {
  "use strict";

  // Spec 035, F4: a click on a feedback request or reply opens the side panel with the conversation.
  const panel = document.getElementById("feedback-panel");
  if (!panel) return;
  const open = (target, link, failed) => {
    const body = target.querySelector(".side-panel-body");
    body.textContent = "Laden…";
    target.hidden = false;
    fetch(link.href, { headers: { "X-Requested-With": "fetch" } })
      .then((response) => (response.ok ? response.text() : Promise.reject(response.status)))
      .then((html) => { body.innerHTML = html; })
      .catch(() => { body.textContent = failed; });
  };
  document.addEventListener("click", (event) => {
    const mark = event.target.closest("[data-feedback]");
    if (mark) {
      event.preventDefault();
      open(panel, mark, "De feedback kon niet worden geladen.");
      return;
    }
    if (event.target.closest("[data-close-panel]")) panel.hidden = true;
  });
  document.addEventListener("keydown", (event) => { if (event.key === "Escape") panel.hidden = true; });
})();

(() => {
  "use strict";

  // Spec 001, F6: place the details of a level cell relative to the window, below the cell when
  // there is room and above it otherwise. Inside a table that scrolls sideways an absolutely
  // positioned tooltip is clipped and gives the table a scroll bar (seen on the bottom rows).
  const GAP = 4;
  const place = (cell) => {
    const tip = cell.querySelector(".level-details");
    if (!tip) return;
    tip.classList.add("is-floating");
    const box = cell.querySelector(".level")?.getBoundingClientRect() || cell.getBoundingClientRect();
    const width = tip.offsetWidth;
    const height = tip.offsetHeight;
    const below = box.bottom + GAP + height <= window.innerHeight;
    const top = below ? box.bottom + GAP : Math.max(GAP, box.top - GAP - height);
    const left = Math.min(Math.max(GAP, box.left + box.width / 2 - width / 2), window.innerWidth - width - GAP);
    tip.style.top = `${top}px`;
    tip.style.left = `${left}px`;
  };
  const reset = (cell) => {
    const tip = cell?.querySelector(".level-details.is-floating");
    if (!tip) return;
    tip.classList.remove("is-floating");
    tip.style.top = "";
    tip.style.left = "";
  };
  document.addEventListener("mouseover", (event) => {
    const cell = event.target.closest(".col-skill");
    if (cell && !cell.contains(event.relatedTarget)) requestAnimationFrame(() => place(cell));
  });
  document.addEventListener("mouseout", (event) => {
    const cell = event.target.closest(".col-skill");
    if (cell && !cell.contains(event.relatedTarget)) reset(cell);
  });
  document.addEventListener("focusin", (event) => {
    const cell = event.target.closest(".col-skill");
    if (cell) requestAnimationFrame(() => place(cell));
  });
  document.addEventListener("focusout", (event) => reset(event.target.closest(".col-skill")));
  // While the page or the table scrolls, keep a visible tooltip next to its cell.
  document.addEventListener("scroll", () => {
    document.querySelectorAll(".level-details.is-floating").forEach((tip) => place(tip.closest(".col-skill")));
  }, true);
})();
