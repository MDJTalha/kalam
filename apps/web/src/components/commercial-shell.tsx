import { PublicHeader } from "./public-header";
import { PublicFooter } from "./public-footer";
import styles from "@/app/commercial.module.css";

export function CommercialShell({ children }: { children: React.ReactNode }) {
  return <div className={styles.page}>
    <a className={styles.skip} href="#commercial-main">Skip to content</a>
    <PublicHeader />
    <main id="commercial-main">{children}</main>
    <PublicFooter />
  </div>;
}
