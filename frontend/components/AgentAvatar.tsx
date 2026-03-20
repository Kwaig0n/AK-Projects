"use client";

interface Props {
  agentType: string;
  isRunning?: boolean;
  size?: number;
}

export function AgentAvatar({ agentType, isRunning = false, size = 48 }: Props) {
  const isRealEstate = agentType === "real_estate";

  return (
    <div
      className="relative flex-shrink-0"
      style={{ width: size, height: size }}
    >
      {/* Gradient circle background */}
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
            ) : (
              <>
                <stop offset="0%" stopColor="#c4b5fd" />
                <stop offset="100%" stopColor="#7c3aed" />
              </>
            )}
          </radialGradient>
        </defs>

        {/* Circle backdrop */}
        <circle cx="24" cy="24" r="24" fill={`url(#grad-${agentType})`} />

        {/* Subtle inner highlight */}
        <ellipse cx="18" cy="14" rx="9" ry="5" fill="white" fillOpacity="0.15" />

        {isRealEstate ? (
          /* House + person silhouette */
          <g fill="white">
            {/* House body */}
            <rect x="13" y="26" width="22" height="13" rx="1" fillOpacity="0.95" />
            {/* Roof */}
            <polygon points="24,13 10,27 38,27" fillOpacity="0.95" />
            {/* Door */}
            <rect x="21" y="31" width="6" height="8" rx="1" fill={isRealEstate ? "#2563eb" : "#7c3aed"} fillOpacity="0.6" />
            {/* Window */}
            <rect x="14" y="28" width="5" height="4" rx="0.5" fill={isRealEstate ? "#2563eb" : "#7c3aed"} fillOpacity="0.5" />
            <rect x="29" y="28" width="5" height="4" rx="0.5" fill={isRealEstate ? "#2563eb" : "#7c3aed"} fillOpacity="0.5" />
          </g>
        ) : (
          /* Researcher / bot silhouette */
          <g fill="white" fillOpacity="0.95">
            {/* Head */}
            <circle cx="24" cy="17" r="6" />
            {/* Body */}
            <path d="M14 38 C14 30 34 30 34 38" />
            {/* Magnifying glass overlay */}
            <circle cx="30" cy="30" r="5" fill="none" stroke="white" strokeWidth="2.5" strokeOpacity="0.9" />
            <line x1="34" y1="34" x2="37" y2="37" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeOpacity="0.9" />
          </g>
        )}
      </svg>

      {/* Running pulse ring */}
      {isRunning && (
        <span className="absolute inset-0 rounded-full animate-ping"
          style={{
            background: isRealEstate
              ? "rgba(37,99,235,0.3)"
              : "rgba(124,58,237,0.3)",
          }}
        />
      )}
    </div>
  );
}
