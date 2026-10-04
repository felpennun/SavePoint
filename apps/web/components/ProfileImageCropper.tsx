"use client";

import { useEffect, useRef, useState } from "react";

const COPY = {
  es: {
    avatarTitle: "Recortar foto de perfil",
    coverTitle: "Recortar portada",
    zoom: "Zoom",
    hint: "Arrastra la imagen para encuadrarla.",
    cancel: "Cancelar",
    confirm: "Usar imagen",
    working: "Procesando…",
    loadError: "No se pudo leer la imagen.",
  },
  en: {
    avatarTitle: "Crop profile photo",
    coverTitle: "Crop cover",
    zoom: "Zoom",
    hint: "Drag the image to frame it.",
    cancel: "Cancel",
    confirm: "Use image",
    working: "Processing…",
    loadError: "The image could not be read.",
  },
} as const;

const VIEWPORT_WIDTH = 320;
const MAX_ZOOM = 3;
const KEY_STEP = 12;

/**
 * Modal crop step shared by the profile photo (circular, square output) and the
 * cover (banner). The picked image is framed with drag and zoom, then redrawn
 * at the output size and compressed in the browser, so what reaches the server
 * is small and already cropped.
 */
export function ProfileImageCropper({
  file,
  shape,
  outWidth,
  outHeight,
  locale,
  onCancel,
  onConfirm,
}: {
  file: File | null;
  shape: "circle" | "banner";
  outWidth: number;
  outHeight: number;
  locale: "es" | "en";
  onCancel: () => void;
  onConfirm: (blob: Blob) => void;
}) {
  const copy = COPY[locale];
  const dialogRef = useRef<HTMLDialogElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const imageRef = useRef<HTMLImageElement | null>(null);
  const dragRef = useRef<{ x: number; y: number; ox: number; oy: number } | null>(null);
  const [ready, setReady] = useState(false);
  const [error, setError] = useState(false);
  const [working, setWorking] = useState(false);
  const [zoom, setZoom] = useState(1);
  const [offset, setOffset] = useState({ x: 0, y: 0 });

  const viewportWidth = shape === "circle" ? 280 : VIEWPORT_WIDTH * 1.5;
  const viewportHeight = Math.round((viewportWidth * outHeight) / outWidth);

  // Open/close the native dialog with the picked file and decode the image.
  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;
    if (!file) {
      if (dialog.open) dialog.close();
      imageRef.current = null;
      setReady(false);
      return;
    }
    setReady(false);
    setError(false);
    setZoom(1);
    setOffset({ x: 0, y: 0 });
    if (!dialog.open) dialog.showModal();
    const url = URL.createObjectURL(file);
    const image = new Image();
    let cancelled = false;
    image.onload = () => {
      if (cancelled) return;
      imageRef.current = image;
      setReady(true);
    };
    image.onerror = () => {
      if (!cancelled) setError(true);
    };
    image.src = url;
    return () => {
      cancelled = true;
      URL.revokeObjectURL(url);
    };
  }, [file]);

  function clampOffset(next: { x: number; y: number }, nextZoom: number, width: number, height: number) {
    const image = imageRef.current;
    if (!image) return next;
    const scale = Math.max(width / image.naturalWidth, height / image.naturalHeight) * nextZoom;
    const maxX = Math.max(0, (image.naturalWidth * scale - width) / 2);
    const maxY = Math.max(0, (image.naturalHeight * scale - height) / 2);
    return { x: Math.min(maxX, Math.max(-maxX, next.x)), y: Math.min(maxY, Math.max(-maxY, next.y)) };
  }

  function paint(
    canvas: HTMLCanvasElement,
    width: number,
    height: number,
    pixelRatio: number,
    currentZoom: number,
    currentOffset: { x: number; y: number },
  ) {
    const image = imageRef.current;
    const context = canvas.getContext("2d");
    if (!image || !context) return;
    canvas.width = Math.round(width * pixelRatio);
    canvas.height = Math.round(height * pixelRatio);
    const scale = Math.max(width / image.naturalWidth, height / image.naturalHeight) * currentZoom * pixelRatio;
    const drawWidth = image.naturalWidth * scale;
    const drawHeight = image.naturalHeight * scale;
    context.fillStyle = "#161826";
    context.fillRect(0, 0, canvas.width, canvas.height);
    context.drawImage(
      image,
      canvas.width / 2 - drawWidth / 2 + currentOffset.x * pixelRatio,
      canvas.height / 2 - drawHeight / 2 + currentOffset.y * pixelRatio,
      drawWidth,
      drawHeight,
    );
  }

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || !ready) return;
    paint(canvas, viewportWidth, viewportHeight, 1, zoom, offset);
  }, [ready, zoom, offset, viewportWidth, viewportHeight]);

  function onPointerDown(event: React.PointerEvent<HTMLDivElement>) {
    if (!ready) return;
    event.currentTarget.setPointerCapture(event.pointerId);
    dragRef.current = { x: event.clientX, y: event.clientY, ox: offset.x, oy: offset.y };
  }

  function onPointerMove(event: React.PointerEvent<HTMLDivElement>) {
    const drag = dragRef.current;
    if (!drag) return;
    setOffset(
      clampOffset(
        { x: drag.ox + event.clientX - drag.x, y: drag.oy + event.clientY - drag.y },
        zoom,
        viewportWidth,
        viewportHeight,
      ),
    );
  }

  function onKeyDown(event: React.KeyboardEvent<HTMLDivElement>) {
    const delta = { ArrowLeft: [KEY_STEP, 0], ArrowRight: [-KEY_STEP, 0], ArrowUp: [0, KEY_STEP], ArrowDown: [0, -KEY_STEP] }[
      event.key
    ];
    if (!delta) return;
    event.preventDefault();
    setOffset((current) =>
      clampOffset({ x: current.x + delta[0], y: current.y + delta[1] }, zoom, viewportWidth, viewportHeight),
    );
  }

  function onZoomChange(value: number) {
    setZoom(value);
    setOffset((current) => clampOffset(current, value, viewportWidth, viewportHeight));
  }

  async function confirm() {
    if (!ready) return;
    setWorking(true);
    const output = document.createElement("canvas");
    paint(output, viewportWidth, viewportHeight, outWidth / viewportWidth, zoom, offset);
    const blob = await new Promise<Blob | null>((resolve) => {
      output.toBlob((webp) => {
        if (webp && webp.type === "image/webp") resolve(webp);
        else output.toBlob(resolve, "image/jpeg", 0.88);
      }, "image/webp", 0.88);
    });
    setWorking(false);
    if (blob) onConfirm(blob);
    else setError(true);
  }

  return (
    <dialog
      ref={dialogRef}
      className="sp-copy-dialog sp-pf-crop-dialog"
      aria-labelledby="pf-crop-title"
      onClose={onCancel}
    >
      <div className="sp-copy-dialog-body">
        <h3 id="pf-crop-title">{shape === "circle" ? copy.avatarTitle : copy.coverTitle}</h3>
        {error ? (
          <p role="alert">{copy.loadError}</p>
        ) : (
          <>
            <div
              className={`sp-pf-crop-viewport${shape === "circle" ? " is-circle" : ""}`}
              style={{ width: viewportWidth, height: viewportHeight }}
              tabIndex={0}
              role="img"
              aria-label={copy.hint}
              onPointerDown={onPointerDown}
              onPointerMove={onPointerMove}
              onPointerUp={() => {
                dragRef.current = null;
              }}
              onKeyDown={onKeyDown}
            >
              <canvas ref={canvasRef} style={{ width: viewportWidth, height: viewportHeight }} />
            </div>
            <p className="sp-meta" style={{ margin: 0 }}>
              {copy.hint}
            </p>
            <label className="sp-pf-zoom">
              <span>{copy.zoom}</span>
              <input
                type="range"
                min={1}
                max={MAX_ZOOM}
                step={0.01}
                value={zoom}
                onChange={(event) => onZoomChange(Number(event.target.value))}
              />
            </label>
          </>
        )}
        <div className="sp-copy-dialog-actions">
          <button type="button" className="sp-copy-cancel" onClick={onCancel}>
            {copy.cancel}
          </button>
          <button type="button" className="sp-btn-primary" onClick={confirm} disabled={!ready || working || error}>
            {working ? copy.working : copy.confirm}
          </button>
        </div>
      </div>
    </dialog>
  );
}
