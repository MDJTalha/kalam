import Link from "next/link";
import type { ButtonHTMLAttributes, MouseEventHandler, ReactNode } from "react";
import styles from "./public-chrome.module.css";

type SharedProps = {
  children: ReactNode;
  variant?: "primary" | "secondary" | "text" | "inverse";
  size?: "sm" | "md" | "lg";
  className?: string;
};

type LinkProps = SharedProps & {
  href: string;
  onClick?: MouseEventHandler<HTMLAnchorElement>;
  type?: never;
  disabled?: never;
};

type ButtonProps = SharedProps & {
  href?: undefined;
  type?: ButtonHTMLAttributes<HTMLButtonElement>["type"];
  disabled?: boolean;
  onClick?: ButtonHTMLAttributes<HTMLButtonElement>["onClick"];
};

export function PublicButton(props: LinkProps | ButtonProps) {
  const {
    children,
    variant = "primary",
    size = "md",
    className = "",
  } = props;
  const classes = `${styles.button} ${styles[variant]} ${styles["size-" + size]} ${className}`;

  if ("href" in props && props.href) {
    return <Link className={classes} href={props.href} onClick={props.onClick}>{children}</Link>;
  }

  return (
    <button
      className={classes}
      type={props.type || "button"}
      disabled={props.disabled}
      onClick={props.onClick as ButtonHTMLAttributes<HTMLButtonElement>["onClick"] | undefined}
    >
      {children}
    </button>
  );
}
