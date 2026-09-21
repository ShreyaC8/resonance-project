"use client";

import dynamic from "next/dynamic";

const Plot = dynamic(() => import("react-plotly.js"), {
    ssr: false,
});

type Track = {
    track_id: string;
    track_name: string;
    artists: string;
    genre: string;
    cluster: number;
    x: number;
    y: number;
};

type TasteMapProps = {
    tracks: Track[];
    userPosition: { x: number; y: number } | null;
};

export default function TasteMap({ tracks, userPosition }: TasteMapProps) {
    return (
        <Plot
            data={[
                {
                    x: tracks.map((track) => track.x),
                    y: tracks.map((track) => track.y),
                    text: tracks.map(
                        (track) => `${track.track_name} — ${track.artists}`
                    ),
                    customdata: tracks.map((track) => [
                        track.genre,
                        track.cluster,
                    ]),
                    mode: "markers",
                    type: "scatter",
                    marker: {
                        size: 8,
                    },
                    hovertemplate:
                        "<b>%{text}</b><br>" +
                        "Genre: %{customdata[0]}<br>" +
                        "Cluster: %{customdata[1]}<extra></extra>",
                },
                {
                    x: userPosition ? [userPosition.x] : [],
                    y: userPosition ? [userPosition.y] : [],
                    text: ["⭐ YOU"],
                    mode: "markers+text",
                    type: "scatter",
                    marker: {
                        size: 18,
                    },
                    textposition: "top center",
                    hovertemplate: "<b>⭐ YOU</b><extra></extra>",
                }
            ]}
            layout={{
                title: "Your Musical Universe",
                xaxis: {
                title: "Musical Dimension 1",
                },
                yaxis: {
                title: "Musical Dimension 2",
                },
                autosize: true,
            }}
            style={{ width: "100%", height: "700px" }}
            useResizeHandler
        />
    );
}