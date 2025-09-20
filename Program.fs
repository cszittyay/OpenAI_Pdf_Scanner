open System
open System.IO
open System.Net.Http
open System.Net.Http.Headers
open System.Text
open System.Text.Json
open System.Text.Json.Nodes

// ================= Config =================
let apiKey =
    match Environment.GetEnvironmentVariable("OPENAI_API_KEY") with
    | null | "" -> failwith "Definí OPENAI_API_KEY en el entorno."
    | v -> v

let model = "gpt-5"   // un modelo multimodal que soporte PDF + JSON mode

let JSON_OPTIONS =
    let o = JsonSerializerOptions(WriteIndented = true)
    o

// ================= Util =================
let uploadPdfAndGetFileId (http: HttpClient) (pdfPath:string) =
    use form = new MultipartFormDataContent()
    let fileContent = new StreamContent(File.OpenRead(pdfPath))
    fileContent.Headers.ContentType <- MediaTypeHeaderValue("application/pdf")
    // purpose recomendado para usar archivos como input del modelo:
    // "user_data" (o el que indique tu flujo) 
    // https://platform.openai.com/docs/guides/pdf-files
    form.Add(StringContent("user_data"), "purpose")
    form.Add(fileContent, "file", Path.GetFileName(pdfPath))

    let resp = http.PostAsync("files", form).Result
    let raw  = resp.Content.ReadAsStringAsync().Result
    if not resp.IsSuccessStatusCode then
        failwithf "Files API error %d: %s" (int resp.StatusCode) raw

    let root = JsonNode.Parse(raw)
    let id = root["id"].GetValue<string>()
    if String.IsNullOrWhiteSpace id then failwithf "No se obtuvo file_id. Respuesta: %s" raw
    id

/// Extrae el JSON desde la estructura de Responses API.
/// En json_object mode, normalmente viene como output_text (string JSON).
let tryExtractJson (root: JsonNode) =
    let output = root["output"] :?> JsonArray
    if isNull output || output.Count = 0 then None else
    let parts = output[0]["content"] :?> JsonArray
    if isNull parts then None else
    // 1) Preferimos output_text (JSON como string)
    let fromText =
        parts
        |> Seq.tryPick (fun p ->
            if p["type"].GetValue<string>() = "output_text" then
                let txt = p["text"].GetValue<string>()
                if isNull txt then None else
                    try
                        let _ = JsonNode.Parse(txt) // valida
                        Some txt
                    with _ -> None
            else None)
    match fromText with
    | Some json -> Some json
    | None ->
        // 2) Fallback: si hubiera un output_json (poco común en json_object mode)
        parts
        |> Seq.tryPick (fun p ->
            if p["type"].GetValue<string>() = "output_json" then
                let js = p["json"]
                if js <> null then Some(js.ToJsonString(JSON_OPTIONS)) else None
            else None)

// ================= Request builder =================
let buildBodyWithFile (model:string) (fileId:string) (instruction:string) =
    // Mensaje del usuario: archivo + instrucción
    let contentArr = JsonArray()

    let partFile = JsonObject()
    partFile["type"]    <- JsonValue.Create("input_file")
    partFile["file_id"] <- JsonValue.Create(fileId)
    contentArr.Add(partFile)

    let partText = JsonObject()
    partText["type"] <- JsonValue.Create("input_text")
    partText["text"] <- JsonValue.Create(instruction)
    contentArr.Add(partText)

    let message = JsonObject()
    message["role"]    <- JsonValue.Create("user")
    message["content"] <- contentArr

    let inputArr = JsonArray()
    inputArr.Add(message)

    // ✅ text.format es un OBJETO con "type"
    let fmt = JsonObject()
    fmt["type"] <- JsonValue.Create("json_object")

    let textObj = JsonObject()
    textObj["format"] <- fmt              // <--- ESTE era el bug

    let root = JsonObject()
    root["model"] <- JsonValue.Create(model)
    root["input"] <- inputArr
    root["text"]  <- textObj

    System.Text.Json.JsonSerializer.Serialize(root)



// ================= Main =================
[<EntryPoint>]
let main argv =
    if argv.Length <> 1 then
        eprintfn "Uso: pdf2json <ruta.pdf>"
        1
    else
        try
            let pdfPath = argv[0]
            if not (File.Exists pdfPath) then failwithf "No existe: %s" pdfPath



            // Instrucción concisa: devolvé SOLO JSON auto-descrito (nada de texto extra).
            // Sugerimos una estructura típica, pero el modelo puede ajustarla según el PDF.
            let instruction =
              "Leé el PDF y devolvé SOLO un objeto JSON auto-descrito con los campos que existan. "               

            

            use http = new HttpClient(BaseAddress = Uri("https://api.openai.com/v1/"))
            http.DefaultRequestHeaders.Authorization <- AuthenticationHeaderValue("Bearer", apiKey)
            http.DefaultRequestHeaders.Accept.Add(MediaTypeWithQualityHeaderValue("application/json"))
                        
            let fileId = uploadPdfAndGetFileId http pdfPath
            let bodyJson =  buildBodyWithFile model fileId instruction
            use content = new StringContent(bodyJson, Encoding.UTF8, "application/json")
            let resp = http.PostAsync("responses", content).Result
            let raw = resp.Content.ReadAsStringAsync().Result

            if not resp.IsSuccessStatusCode then
                eprintfn "HTTP %d\n%s" (int resp.StatusCode) raw
                2
            else
                let root = JsonNode.Parse(raw)
                match tryExtractJson root with
                | Some json ->
                    // stdout -> único paso de "decodificación"
                    printfn "%s" json
                    0
                | None ->
                    eprintfn "No se encontró contenido JSON en la respuesta.\nRespuesta: %s" raw
                    3
        with ex ->
            eprintfn "Error: %s" ex.Message
            1
