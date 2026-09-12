/**
 * One shared, idempotent enhancement for every `.sp-dropdown` on the page
 * (FilterDropdown, FacetMenu): clicking outside an open dropdown closes it,
 * Escape closes the focused one, and opening one closes any other that was
 * already open. All three are progressive enhancements -- every dropdown is
 * a plain <details>/<summary> and stays fully usable (just permanently
 * expandable one at a time via native toggling) with JavaScript off.
 *
 * Rendered once per filter toolbar (catalogue's FilterBar, the collection
 * page's own controls form). The init guard makes a second render on the
 * same page a no-op rather than a duplicate set of listeners.
 */
export function FilterDropdownScript() {
  return (
    <script
      dangerouslySetInnerHTML={{
        __html: `(() => {
          if (window.__spFilterDropdownInit) return;
          window.__spFilterDropdownInit = true;
          const openDropdowns = () => document.querySelectorAll("details.sp-dropdown[open]");
          document.addEventListener("click", (event) => {
            openDropdowns().forEach((d) => {
              if (!d.contains(event.target)) d.removeAttribute("open");
            });
          });
          document.addEventListener("toggle", (event) => {
            const el = event.target;
            if (!(el && el.matches && el.matches("details.sp-dropdown") && el.open)) return;
            openDropdowns().forEach((d) => {
              if (d !== el) d.removeAttribute("open");
            });
          }, true);
          document.addEventListener("keydown", (event) => {
            if (event.key !== "Escape") return;
            const open = document.querySelector("details.sp-dropdown[open]");
            if (!open) return;
            open.removeAttribute("open");
            const trigger = open.querySelector("summary");
            if (trigger) trigger.focus();
          });
        })();`,
      }}
    />
  );
}
