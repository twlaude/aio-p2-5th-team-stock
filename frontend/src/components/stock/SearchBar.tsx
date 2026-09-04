import { ArrowRight, Search } from "lucide-react";
import { useEffect, useState, type ChangeEvent, type FormEvent } from "react";

import type { SearchStatus } from "../../state/searchStore";
import { handleSearchSubmit } from "./searchSubmit";
import "./searchBar.css";

interface SearchBarProps {
  value: string;
  status: SearchStatus;
  unsupported: boolean;
  onChange: (value: string) => void;
  onSubmit: (query: string) => void;
  onTypingChange?: (typing: boolean) => void;
}

export function SearchBar({ value, status, unsupported, onChange, onSubmit, onTypingChange }: SearchBarProps) {
  const [focused, setFocused] = useState(false);
  const typing = focused && value.trim().length > 0;

  useEffect(() => {
    onTypingChange?.(typing);
  }, [onTypingChange, typing]);

  const submit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (handleSearchSubmit(value, onSubmit)) {
      onTypingChange?.(false);
    }
  };

  const change = (event: ChangeEvent<HTMLInputElement>) => {
    onChange(event.target.value);
  };

  // motion 4b-3, motion 4b-15, motion 4b-18
  return (
    <form className={`search-bar${focused ? " search-bar--focus" : ""}${unsupported ? " search-bar--shake" : ""}`} onSubmit={submit}>
      <Search className="search-bar__icon" size={22} strokeWidth={2} aria-hidden="true" />
      <input
        className="search-bar__input"
        aria-label="기업명 또는 종목코드 6자리"
        value={value}
        onBlur={() => setFocused(false)}
        onChange={change}
        onFocus={() => setFocused(true)}
        placeholder="기업명 또는 종목코드 6자리"
      />
      <button className="search-bar__button" type="submit" disabled={status === "loading"}>
        <span>살펴보기</span>
        <ArrowRight size={16} strokeWidth={2.2} aria-hidden="true" />
      </button>
    </form>
  );
}
