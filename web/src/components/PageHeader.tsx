export function PageHeader({ title, lede }: { title: string; lede?: string }) {
  return (
    <header className="mb-6">
      <h1 className="font-heading text-[27px] leading-tight text-ink sm:text-[30px]">{title}</h1>
      {lede && <p className="mt-2 max-w-3xl text-[15px] text-body">{lede}</p>}
    </header>
  );
}
