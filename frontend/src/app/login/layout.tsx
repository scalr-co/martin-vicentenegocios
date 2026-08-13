export default function LoginLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <>
      <style>{`
        html, body {
          background: #12100e !important;
          min-height: 100%;
          min-height: 100dvh;
        }
        html.dark, html.dark body {
          background: #0c0a09 !important;
        }
      `}</style>
      {children}
    </>
  );
}
