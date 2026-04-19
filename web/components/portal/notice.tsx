import clsx from "clsx";

const toneClasses = {
  neutral: "border-line bg-mist text-ink/72",
  success: "border-pine/20 bg-pine/10 text-pine",
  warning: "border-[#AA8A24]/20 bg-[#F8E7A6] text-[#6D5613]",
  error: "border-berry/20 bg-berry/10 text-berry",
};

export function Notice({
  title,
  copy,
  tone = "neutral",
}: {
  title: string;
  copy: string;
  tone?: keyof typeof toneClasses;
}) {
  return (
    <div className={clsx("rounded-[8px] border p-4", toneClasses[tone])}>
      <p className="text-sm font-semibold">{title}</p>
      <p className="mt-2 text-sm leading-6">{copy}</p>
    </div>
  );
}
