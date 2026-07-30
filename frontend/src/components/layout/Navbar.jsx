// import { Icon } from "../ui/Icons";

// export default function Navbar({
//   hasUploaded,
//   uploadedInfo,
//   onExport,
// }) {
//   return (
//     <nav className="ds-nav">
//       <div className="ds-logo">DataSage</div>

//       <div className="ds-nav-right">
//         {hasUploaded && (
//           <>
//             <div className="ds-nav-pill">
//               <Icon.File />

//               {uploadedInfo.name}

//               {uploadedInfo.rows !== "—" && (
//                 <span
//                   style={{
//                     color: "#9CA3AF",
//                     marginLeft: 4,
//                   }}
//                 >
//                   ({Number(uploadedInfo.rows).toLocaleString()} rows)
//                 </span>
//               )}
//             </div>

//             <button
//               className="ds-download-btn"
//               onClick={onExport}
//             >
//               <Icon.Download />
//               Download Report
//             </button>
//           </>
//         )}

//         <div className="ds-nav-icon">
//           <Icon.Bell />
//         </div>

//         <div className="ds-nav-icon">
//           <Icon.User />
//         </div>
//       </div>
//     </nav>
//   );
// }



import { Icon } from "../ui/Icons";

export default function Navbar({
  hasUploaded,
  uploadedInfo,
  onExport,
}) {
  return (
    <nav className="ds-nav">

      <div className="ds-nav-brand">
        <img
          src="/favicon.png"
          alt="DataSage"
          className="ds-nav-logo"
        />

        <div className="ds-logo">
          DataSage
        </div>
      </div>

      <div className="ds-nav-right">

        {!hasUploaded && (
          <div className="ds-nav-tagline">
            AI-powered Data Analytics
          </div>
        )}

        {hasUploaded && (
          <>
            <div className="ds-nav-pill">
              <Icon.File />

              {uploadedInfo.name}

              {uploadedInfo.rows !== "—" && (
                <span className="ds-nav-pill-count">
                  ({Number(uploadedInfo.rows).toLocaleString()} rows)
                </span>
              )}
            </div>

            {/* <button
              className="ds-download-btn"
              onClick={onExport}
            >
              <Icon.Download />
              Download Report
            </button> */}
          </>
        )}

      </div>

    </nav>
  );
}