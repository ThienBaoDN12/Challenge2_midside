import { useEffect, useId, useRef, useState } from "react";
import { Check, ChevronDown } from "lucide-react";

/**
 * Styled replacement for <select>.
 * options: array of strings or { value, label }.
 * Works controlled (value + onChange) or uncontrolled (defaultValue / value without onChange).
 */
export default function Dropdown({
  value,
  defaultValue,
  options,
  onChange,
  icon,
  prefix,
  variant = "field",
  ariaLabel,
}) {
  const items = options.map((o) =>
    typeof o === "string" ? { value: o, label: o } : o,
  );
  const [inner, setInner] = useState(value ?? defaultValue ?? items[0]?.value);
  const current = onChange ? value : inner;
  const [open, setOpen] = useState(false);
  const [active, setActive] = useState(0);
  const [dropUp, setDropUp] = useState(false);
  const root = useRef(null);
  const listId = useId();

  const selected = items.find((i) => i.value === current) ?? items[0];

  useEffect(() => {
    if (!open) return;
    const close = (e) => {
      if (!root.current?.contains(e.target)) setOpen(false);
    };
    document.addEventListener("mousedown", close);
    return () => document.removeEventListener("mousedown", close);
  }, [open]);

  function openMenu() {
    setActive(
      Math.max(
        0,
        items.findIndex((i) => i.value === current),
      ),
    );
    // Open upward when there is not enough room below the trigger
    const rect = root.current.getBoundingClientRect();
    setDropUp(window.innerHeight - rect.bottom < 300 && rect.top > 300);
    setOpen(true);
  }

  function choose(item) {
    if (onChange) onChange(item.value);
    else setInner(item.value);
    setOpen(false);
  }

  function onKeyDown(e) {
    if (!open) {
      if (["ArrowDown", "ArrowUp", "Enter", " "].includes(e.key)) {
        e.preventDefault();
        openMenu();
      }
      return;
    }
    if (e.key === "Escape" || e.key === "Tab") setOpen(false);
    else if (e.key === "ArrowDown") {
      e.preventDefault();
      setActive((a) => (a + 1) % items.length);
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setActive((a) => (a - 1 + items.length) % items.length);
    } else if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      choose(items[active]);
    }
  }

  return (
    <div
      className={`dropdown dropdown--${variant} ${open ? "is-open" : ""} ${dropUp ? "drop-up" : ""}`}
      ref={root}
    >
      <button
        type="button"
        className="dropdown__trigger"
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-controls={listId}
        aria-label={ariaLabel}
        onClick={() => (open ? setOpen(false) : openMenu())}
        onKeyDown={onKeyDown}
      >
        {icon && <span className="dropdown__icon">{icon}</span>}
        {prefix && <span className="dropdown__prefix">{prefix}</span>}
        <span className="dropdown__value">{selected?.label}</span>
        <ChevronDown
          className="dropdown__chevron"
          size={16}
          aria-hidden="true"
        />
      </button>

      {open && (
        <ul className="dropdown__menu" role="listbox" id={listId}>
          {items.map((item, i) => {
            const isSelected = item.value === current;
            return (
              <li
                key={item.value}
                role="option"
                aria-selected={isSelected}
                className={`dropdown__option ${i === active ? "is-active" : ""} ${isSelected ? "is-selected" : ""}`}
                onMouseEnter={() => setActive(i)}
                onMouseDown={(e) => e.preventDefault()}
                onClick={() => choose(item)}
              >
                <span>{item.label}</span>
                {isSelected && <Check size={15} aria-hidden="true" />}
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
