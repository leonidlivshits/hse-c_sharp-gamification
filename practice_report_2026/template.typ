#let template(cfg: none, body) = {
    assert(cfg != none)
    assert(cfg.project != none)
    assert(cfg.project.name != none)
    assert(cfg.student != none)
    assert(cfg.student.name != none)
    assert(cfg.student.short_name != none)
    assert(cfg.student.group != none)
    assert(cfg.student.accepted_date != none)
    assert(cfg.agreed_by.name != none)
    assert(cfg.agreed_by.position != none)
    assert(cfg.approved_by.name != none)
    assert(cfg.approved_by.position != none)
    assert(cfg.university_name != none)
    assert(cfg.faculty_name != none)
    assert(cfg.edu_program_name != none)
    assert(cfg.city != none)
    assert(cfg.year != none)

    let un(n) = "_" * n

    let title_page = {
        let top_banner = [
            #set par(spacing: 0.45em)
            #set text(size: 14pt)

            #text(weight: "bold", cfg.university_name)

            #cfg.faculty_name

            #cfg.edu_program_name
        ]

        let report_title = [
            #set align(center)
            #set par(spacing: 0.65em)
            #set text(size: 14pt, weight: "bold")

            ОТЧЕТ

            #set text(size: 14pt, weight: "regular")

            по производственной практике

            #v(3mm)

            #set text(size: 14pt)

            #cfg.org.practice_place

            в (на) #cfg.org.name
        ]

        let org_supervisor_block = [
            #set align(left)
            #set text(size: 14pt)
            #set par(spacing: 0.45em)

            Руководитель практики от профильной организации

            #grid(
                columns: (1fr, 35mm, 38mm),
                column-gutter: 4mm,
                align: horizon,
                [#cfg.agreed_by.position],
                align(center)[#line(length: 30mm)],
                align(center)[#cfg.agreed_by.name],
                text(size: 14pt)[(должность)],
                align(center)[#text(size: 14pt)[(подпись)]],
                align(center)[#text(size: 14pt)[(фамилия, инициалы)]],
            )

            Дата: #line(length: 35mm)
        ]

        let student_accept_block = [
            #set align(left)
            #set text(size: 14pt)
            #set par(spacing: 0.45em)

            Задание принято к исполнению #h(1fr) #cfg.student.accepted_date

            Студент

            #grid(
                columns: (1fr, 35mm, 38mm),
                column-gutter: 4mm,
                align: horizon,
                [группы #cfg.student.group],
                align(center)[#line(length: 30mm)],
                align(center)[#cfg.student.short_name],
                [],
                align(center)[#text(size: 14pt)[(подпись)]],
                align(center)[#text(size: 14pt)[(фамилия, инициалы)]],
            )
        ]

        let hse_supervisor_block = [
            #set align(left)
            #set text(size: 14pt)
            #set par(spacing: 0.45em)

            #text(weight: "bold")[СОГЛАСОВАНО]

            Руководитель практики от НИУ ВШЭ:

            #grid(
                columns: (1fr, 35mm, 38mm),
                column-gutter: 4mm,
                align: horizon,
                [#cfg.approved_by.position],
                align(center)[#line(length: 30mm)],
                align(center)[#cfg.approved_by.name],
                text(size: 14pt)[Должность, место работы],
                align(center)[#text(size: 14pt)[(подпись)]],
                align(center)[#text(size: 14pt)[И.О.Фамилия]],
            )

            Дата: #line(length: 35mm)
        ]

        let bottom_banner = [
            #set align(center)
            #set text(size: 14pt)
            #cfg.city - #cfg.year
        ]

        page(
            header: none,
            footer: none,
            margin: (
                left: 30mm,
                right: 10mm,
                top: 20mm,
                bottom: 20mm,
            )
        )[
            #set align(center)

            #grid(
                columns: (1fr),
                row-gutter: 9mm,
                top_banner,
                report_title,
                org_supervisor_block,
                student_accept_block,
                hse_supervisor_block,
                bottom_banner,
            )
        ]

        counter(page).update(1)
    }

    let outline_block = {
        pagebreak(weak: true)

        {
            set align(center)
            set text(weight: "bold")
            [СОДЕРЖАНИЕ]
        }

        outline(
            title: none,
            indent: 5mm,
        )
    }

    let normal_pages = {
        set page(
            margin: (
                top: 20mm,
                left: 30mm,
                right: 10mm,
                bottom: 20mm,
            ),
            header: [
                #set align(center)
                #set text(weight: "bold")
                #context counter(page).display()
            ],
            footer: []
        )

        set par(
            justify: true,
            leading: 1.35em,
            first-line-indent: 1.25cm,
        )

        set heading(numbering: "1.")

        show heading.where(level: 1): h => {
            set align(center)
            set text(weight: "bold", size: 14pt)

            pagebreak(weak: true)
            if h.numbering != none [
                #counter(heading).display(h.numbering) #h.body
            ] else [
                #h.body
            ]
        }

        show heading.where(level: 2): h => {
            set text(weight: "bold", size: 14pt)
            [#counter(heading).display() #h.body]
        }

        pagebreak(weak: true)
        align(center, text(weight: "bold", size: 14pt, [АННОТАЦИЯ]))
        cfg.annotation

        outline_block
        body
    }

    set text(
        lang: "ru",
        size: 14pt,
        font: "Times New Roman"
    )

    title_page
    normal_pages
}
