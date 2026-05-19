"use client";

interface Props {
  agentType: string;
  isRunning?: boolean;
  size?: number;
}

export function AgentAvatar({ agentType, isRunning = false, size = 48 }: Props) {
  const isRealEstate = agentType === "real_estate";
  const isJobListing = agentType === "job_listing";

  const pulseColor = isRealEstate
    ? "rgba(37,99,235,0.3)"
    : isJobListing
    ? "rgba(5,150,105,0.3)"
    : "rgba(124,58,237,0.3)";

  return (
    <div
      className="relative flex-shrink-0"
      style={{ width: size, height: size }}
    >
      <svg
        width={size}
        height={size}
        viewBox="0 0 48 48"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
      >
        <defs>
          <radialGradient id={`grad-${agentType}`} cx="40%" cy="35%" r="65%">
            {isRealEstate ? (
              <>
                <stop offset="0%" stopColor="#6ee7f7" />
                <stop offset="100%" stopColor="#2563eb" />
              </>
            ) : isJobListing ? (
              <>
                <stop offset="0%" stopColor="#6ee7b7" />
                <stop offset="100%" stopColor="#059669" />
              </>
            ) : (
              <>
                <stop offset="0%" stopColor="#c4b5fd" />
                <stop offset="100%" stopColor="#7c3aed" />
              </>
            )}
          </radialGradient>
        </defs>

        <circle cx="24" cy="24" r="24" fill={`url(#grad-${agentType})`} />
        <ellipse cx="18" cy="14" rx="9" ry="5" fill="white" fillOpacity="0.15" />

        {isRealEstate ? (
          <g fill="white">
            <rect x="13" y="26" width="22" height="13" rx="1" fillOpacity="0.95" />
            <polygon points="24,13 10,27 38,27" fillOpacity="0.95" />
            <rect x="21" y="31" width="6" height="8" rx="1" fill="#2563eb" fillOpacity="0.6" />
            <rect x="14" y="28" width="5" height="4" rx="0.5" fill="#2563eb" fillOpacity="0.5" />
            <rect x="29" y="28" width="5" height="4" rx="0.5" fill="#2563eb" fillOpacity="0.5" />
          </g>
        ) : isJobListing ? (
          /* Briefcase silhouette */
          <g fill="white" fillOpacity="0.95">
            {/* Briefcase body */}
            <rect x="10" y="22" width="28" height="18" rx="2" />
            {/* Briefcase handle */}
            <path d="M19 22 L19 18 Q19 16 21 16 L27 16 Q29 16 29 18 L29 22" fill="none" stroke="white" strokeWidth="2.5" strokeOpacity="0.9" />
            {/* Centre clasp line */}
            <rect x="10" y="29" width="28" height="2" fill="#059669" fillOpacity="0.5" />
            <rect x="22" y="27" width="4" height="6" rx="1" fill="#059669" fillOpacity="0.6" />
          </g>
        ) : (
          <g fill="white" fillOpacity="0.95">
            <circle cx="24" cy="17" r="6" />
            <path d="M14 38 C14 30 34 30 34 38" />
            <circle cx="30" cy="30" r="5" fill="none" stroke="white" strokeWidth="2.5" strokeOpacity="0.9" />
            <line x1="34" y1="34" x2="37" y2="37" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeOpacity="0.9" />
          </g>
        )}
      </svg>

      {isRunning && (
        <span className="absolute inset-0 rounded-full animate-ping"
          style={{ background: pulseColor }}
        />
      )}
    </div>
  );
}
