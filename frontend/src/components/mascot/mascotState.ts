import type { SearchStatus } from "../../state/searchStore";
import type { MascotState } from "./Mascot";

export interface HeroMascotInput {
  status: SearchStatus;
  typing: boolean;
  unsupported: boolean;
  errored: boolean;
}

export function mascotClassName(state: MascotState, className?: string): string {
  return ["mascot", `mascot--${state}`, className].filter(Boolean).join(" ");
}

export function heroMascotState(input: HeroMascotInput): MascotState {
  if (input.errored || input.unsupported) {
    return "oops";
  }

  if (input.status === "loading") {
    return "thinking";
  }

  return input.typing ? "typing" : "idle";
}
