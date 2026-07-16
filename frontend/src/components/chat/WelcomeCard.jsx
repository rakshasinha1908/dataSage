// import { Icon } from "../ui/Icons";

// export default function WelcomeCard({ uploadedInfo }) {
//   return (
//     <div className="ds-msg">
//       <div className="ds-msg-header">
//         <div className="ds-avatar-gradient">
//           <Icon.Sparkle />
//         </div>

//         <div>
//           <div className="ds-msg-name">DataSage</div>
//           <div className="ds-msg-sub">AI Analyst</div>
//         </div>
//       </div>

//       <div className="ds-welcome-card">
//         <div className="ds-welcome-title">
//           Ready to analyse <em>{uploadedInfo.name}</em>
//         </div>

//         <div className="ds-welcome-sub">
//           Ask anything — I can show top/bottom rows, averages,
//           trends, distributions, comparisons, or open-ended
//           questions.
//         </div>

//         {uploadedInfo.summary && (
//           <div className="ds-summary-card">
//             <div className="ds-summary-label">
//               <Icon.Sparkle /> Dataset Summary
//             </div>

//             <p>{uploadedInfo.summary}</p>
//           </div>
//         )}
//       </div>
//     </div>
//   );
// }



import { Icon } from "../ui/Icons";
import SparkleAvatar from "./SparkleAvatar";

export default function WelcomeCard({ uploadedInfo }) {
  return (
    <div className="ds-msg">
      <div className="ds-msg-header">
        <SparkleAvatar />

        <div>
          <div className="ds-msg-name">DataSage</div>
          <div className="ds-msg-sub">AI Analyst</div>
        </div>
      </div>

      <div className="ds-welcome-card">
        <div className="ds-welcome-title">
          Ready to analyse <em>{uploadedInfo.name}</em>
        </div>

        <div className="ds-welcome-sub">
          Ask anything — I can show top/bottom rows,
          averages, trends, distributions,
          comparisons, or open-ended questions.
        </div>

        {uploadedInfo.summary && (
          <div className="ds-summary-card">
            <div className="ds-summary-label">
              <Icon.Sparkle />
              Dataset Summary
            </div>

            <p>{uploadedInfo.summary}</p>
          </div>
        )}
      </div>
    </div>
  );
}