Frontend Design Doc

Project: Local Business Matching Platform
Frontend Stack: Leaflet + TypeScript

1. Purpose

The frontend should help users quickly understand which local businesses are the best fit for a candidate based on location, website content, and hiring relevance. It should turn a large set of business data into a simple, trustworthy, recruiter-friendly interface.

2. Primary Goal

Build a clear map-based experience that lets a user:

view local businesses geographically,
filter and search them quickly,
inspect why a business matches a resume,
and produce a clean shortlist for recruiter outreach.
3. Users

The main users are:

internal recruiters or outreach users who need a ranked list of businesses to contact,
admins/researchers who need to review business details and correct bad data.
4. Frontend Goals
A. Make location intuitive

The user should immediately understand where businesses are located relative to the candidate or target area.

B. Make matching explainable

The UI should not only show a score. It should show why a business is a match, using visible skill, industry, and website-based signals.

C. Keep the workflow fast

A recruiter should be able to move from map view to business detail to shortlist creation without friction.

D. Support trust and correction

The frontend should make it easy to spot weak matches, missing data, or incorrect locations so users can improve quality over time.

5. Non-Goals

The frontend is not trying to:

be a GIS-heavy professional mapping tool,
perform the matching logic itself,
replace backend scraping, ranking, or data cleaning,
or optimize for visual complexity over usability.
6. Core Screens
1. Map View

Main screen with Leaflet map and business markers.

2. Filter Panel

Simple controls for radius, industry, semantic fit threshold, and hiring/contact signals.

3. Business Detail Panel

A side panel or popup showing:

business name,
website,
distance,
fit score,
reason for match,
contact information,
outreach status.
4. Saved List / Shortlist View

A clean list of selected businesses for recruiter follow-up.

7. Design Principles
Simple first

The interface should feel lightweight and obvious, not crowded.

Map-first, but not map-only

The map should be the anchor, but list and detail views should be equally useful.

Explain every score

Every important recommendation should have visible reasoning.

Fast interaction

Clicking a marker, opening details, and applying filters should feel immediate.

Editable data

Users should be able to flag or correct bad records without leaving the workflow.

8. Technical Frontend Direction
Leaflet will be used for map rendering and marker interaction.
TypeScript will be used to keep map state, filter state, and business data strongly typed.
The frontend should be built from reusable components rather than one large page script.
The first version should favor simplicity over abstraction.
9. Initial Success Criteria

The frontend is successful if a recruiter can:

open the map,
filter businesses near a target location,
understand why a business matches a candidate,
save the strongest businesses,
and leave with a usable outreach list.
10. First Version Priority

For the first release, the frontend should prioritize:

stable map rendering,
clean filters,
clear business detail display,
visible match explanations,
and a shortlist workflow.