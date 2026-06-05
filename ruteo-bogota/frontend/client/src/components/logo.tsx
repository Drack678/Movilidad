export function Logo({ className = "", size = 28 }: { className?: string; size?: number }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 32 32"
      fill="none"
      className={className}
      aria-label="RutaBogá"
      role="img"
    >
      <path
        d="M9 23 C9 16, 17 17, 17 11 C17 7.5, 14 7, 12 8.5"
        stroke="currentColor"
        strokeWidth="2.4"
        strokeLinecap="round"
        fill="none"
        strokeDasharray="0.1 4.2"
      />
      <circle cx="9" cy="23" r="3" fill="currentColor" />
      <circle cx="23" cy="10" r="3.4" className="fill-chart-3" stroke="currentColor" strokeWidth="1.2" />
    </svg>
  );
}

export function Wordmark({ className = "" }: { className?: string }) {
  return (
    <span className={`flex items-center gap-2 ${className}`}>
      <Logo size={26} className="text-primary" />
      <span className="font-display text-lg font-extrabold tracking-tight">
        Ruta<span className="text-primary">Bogá</span>
      </span>
    </span>
  );
}
